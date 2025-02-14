import json
import subprocess
import os
import log as Log
import urllib.request
import datetime
from config import AppConfig
from azure.identity import DefaultAzureCredential
from azure.mgmt.subscription import SubscriptionClient
import pandas as pd
import zlib
import sys
from wara.model import Subscription
from pathlib import Path
sys.path.append(str(Path(__file__).absolute().parent))
from db import DB

class RunContext:
   def __init__(self):
      self.run_start_time = datetime.datetime.now()
      

class WARAExecutor:

   def __init__(self, config: AppConfig):
      file_full_path = os.path.realpath(__file__)
      cwd = os.path.dirname(file_full_path)
      self.db = DB(config)

      self.config = config
      self.exec_root_dir = os.path.join(cwd, 'temp_wara_exec') #, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
      self.collector_ps1_url = 'https://github.com/Azure/Azure-Proactive-Resiliency-Library-v2/raw/refs/heads/main/tools/1_wara_collector.ps1'
      self.analyzer_ps1_url = 'https://raw.githubusercontent.com/Azure/Azure-Proactive-Resiliency-Library-v2/refs/heads/main/tools/2_wara_data_analyzer.ps1'
      self.wara_report_generator_ps1_url = 'https://raw.githubusercontent.com/Azure/Azure-Proactive-Resiliency-Library-v2/refs/heads/main/tools/3_wara_reports_generator.ps1'
      self.collector_script_wrapper_path = os.path.join(cwd, 'wara_collector_script_wrapper.ps1')
      self.collector_ps1_file_path = os.path.join(self.exec_root_dir, '1_wara_collector.ps1')
      self.analyzer_ps1_file_path = os.path.join(self.exec_root_dir, '2_wara_data_analyzer.ps1')
      self.wara_report_generator_ps1_file_path = os.path.join(self.exec_root_dir, '3_wara_reports_generator.ps1')
      

   # create temp folder for execution. All execution files will be stored here.
   def _create_root_exec_dir(self):
      Log.debug('WARA - create root exec dir')
      if not os.path.exists(self.exec_root_dir):
         os.makedirs(self.exec_root_dir)

   def _del_root_exec_dir(self):
      os.rmdir(self.exec_root_dir)


   def generate_execution_id(self) -> list[datetime.datetime, str]:
      now = datetime.datetime.now()
      execution_start_time =  now.strftime("%a %d %b %Y %H:%M:%S")
      execution_id = str(now.timestamp())
      return execution_start_time, execution_id
   
   # download scripts
   # 1_wara_collector.ps1
   # 2_wara_data_analyzer.ps1
   # 3_wara_reports_generator.ps1
   def _download_scripts(self):
      urllib.request.urlretrieve(self.collector_ps1_url, self.collector_ps1_file_path )
      urllib.request.urlretrieve(self.analyzer_ps1_url, self.analyzer_ps1_file_path)
      urllib.request.urlretrieve(self.wara_report_generator_ps1_url, self.wara_report_generator_ps1_file_path)


   # get subscription ids
   def get_subscriptions(self):
      result = []

      client = SubscriptionClient(DefaultAzureCredential())

      subscription_list  = client.subscriptions.list()

      for sub in subscription_list:
         result.append(Subscription(sub.subscription_id, sub.display_name))

      Log.debug(f'WARA - subscription fetched successfully {result}')

      return result

   # run collector script
   def _exec_collector_ps1(self, subscription_id: str) -> str:

      '''
      returns json file path
      '''
      
      #cmd = f'pwsh -c Connect-AzAccount -Identity -TenantId {self.config.wara_tenantId} && ./1_wara_collector.ps1 -tenantid {self.config.wara_tenantId} -subscriptionids {subscription_ids}'
      cmd = f'pwsh {self.collector_script_wrapper_path} -tenantid {self.config.wara_tenantId} -subscriptionids {subscription_id}'

      Log.debug(f'WARA - executing collector.ps1 with cmd: {cmd}')

      p = subprocess.Popen(cmd, 
                           shell=True,
                           text=True,
                           stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
      
      try:
         while True:
            line = p.stdout.readline()
            if not line:
               break
            #Log.debug(f'WARA - {line.rstrip()}')

         p.wait(timeout=3)

         Log.debug(f'WARA - finish executing collector.ps1')

      except subprocess.TimeoutExpired:
         p.kill(p.pid)
         Log.debug(f'WARA - finish executing collector.ps1')
      

      for file in os.listdir(self.exec_root_dir):
            if file.endswith(".json"):
               fp = os.path.join(self.exec_root_dir, file)
               Log.debug(f'WARA - executed collector.ps1 sucessfully, output json file {fp}')
               return fp
      
      Log.debug(f'WARA - collector.ps1 failed execution, no json output file found')

   # run analyzer script
   def exec_analyzer_ps1(self, json_file_path) -> str:
      '''
      returns json file file
      '''

      if not json_file_path:
         Log.exception('WARA - cannot find collector.ps1 json file result')
         return

      cmd = f'pwsh {self.analyzer_ps1_file_path} -JSONFile {json_file_path}'

      Log.debug(f'WARA - executing wara_data_analyzer.ps1 with cmd: {cmd}')

      p = subprocess.Popen(cmd, 
                           shell=True,
                           text=True,
                           stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
      
      
      try:
         while True:
            line = p.stdout.readline()
            if not line:
               break
            #Log.debug(f'WARA - {line.rstrip()}') #reduce logging

         p.wait(timeout=3)
         
         Log.debug(f'WARA - finish executing wara_data_analyzer.ps1')

      except subprocess.TimeoutExpired:
         p.kill(p.pid)
         Log.debug(f'WARA - finish executing wara_data_analyzer.ps1')

      
      for file in os.listdir(self.exec_root_dir):
            if file.endswith(".xlsx"):
               fp = os.path.join(self.exec_root_dir, file)
               Log.debug(f'WARA - executed wara_data_analyzer.ps1 sucessfully, output Excel file. {fp}')
               return fp
     
      Log.debug(f'WARA - wara_data_analyzer.ps1 failed execution, no Excel output file found')

   def read_and_save_recommendations_json(self, file_path: str, execution_id, subscription_id) -> list[bool, str]:
         try:
            
            # worksheet may not exist, catch and return True
            try:
               df = pd.read_excel(file_path, 'Recommendations')
            except Exception as e:
               return True, ''

            jdf = df.to_json(orient='records')

            compressed = self.compress_string(jdf)

            entity = {
               'PartitionKey': subscription_id,
               'RowKey': execution_id,
               'data': compressed
            }

            self.db.insert(self.db.wara_recommendation_table_name, entity)

            return True, ''
            
         except Exception as e:
            Log.exception(e)
            return False, str(e)
         
      
   def read_impacted_resources_json(self,subscription_id, execution_id, file_path: str) -> list[bool, str]:
      try:
         # worksheet may not exist, catch and return True
         try:
            df = pd.read_excel(file_path, 'ImpactedResources')
         except:
            return True, ''
      

         json = df.to_json(orient='records')

         compressed = self.compress_string(json)

         entity = {
            'PartitionKey': subscription_id,
            'RowKey': execution_id,
            'data': compressed
         }

         self.db.insert(self.db.wara_impacted_resources_table_name, entity)

         return True, ''
      
      except Exception as e:
         Log.exception(e)
         return False, str(e)

   def read_resource_types_json(self, subscription_id, execution_id, file_path: str) -> list[bool, str]:
      try:
         # worksheet may not exist, catch and return True
         try:
            df = pd.read_excel(file_path, 'ResourceTypes')
         except:
            return True, ''
      
         
         json = df.to_json(orient='records')

         compressed = self.compress_string(json)

         entity = {
            'PartitionKey': subscription_id,
            'RowKey': execution_id,
            'data': compressed
         }

         self.db.insert(self.db.wara_resource_type_table_name, entity)

         return True, ''
      
      except Exception as e:
         Log.exception(e)
         return False, str(e)

   def read_retirements_json(self, subscription_id, execution_id, file_path: str) -> list[bool, str]:
      try:

         # worksheet may not exist, catch and return True
         try:
            df = pd.read_excel(file_path, 'Retirements')
         except:
            return True, ''

         json = df.to_json(orient='records')

         compressed = self.compress_string(json)

         entity = {
            'PartitionKey': subscription_id,
            'RowKey': execution_id,
            'data': compressed
         }

         self.db.insert(self.db.wara_retirements_table_name, entity)

         return True, ''

      except Exception as e:
         Log.exception(e)
         return False, str(e)
      

   # pandas read excel from Excel
   def read_and_save_analyzer_excel_result(self, excel_file_path, subscription_id: str, execution_id: str):

      try:

         if not excel_file_path:
            Log.exception('WARA - cannot find analyzer.ps1 Excel file result')
            return False
         
         r_ok, r_err = self.read_and_save_recommendations_json(excel_file_path, execution_id, subscription_id)

         if not r_ok:
            Log.exception(f'WARA - error reading Excel Recommendation worksheet. {r_err}')

         i_ok, i_err = self.read_impacted_resources_json(subscription_id, execution_id, excel_file_path)

         if not i_ok:
            Log.exception(f'WARA - error reading Excel Impacted Resources worksheet. {i_err}')


         rt_ok, rt_err = self.read_resource_types_json(subscription_id, execution_id, excel_file_path)

         if not rt_ok:
            Log.exception(f'WARA - error reading Excel Resource Type worksheet. {rt_err}')

         ret_ok, ret_err = self.read_retirements_json(subscription_id, execution_id, excel_file_path)

         if not ret_ok:
            Log.exception(f'WARA - error reading Excel Retirement worksheet. {ret_err}')
      

      except Exception as e:
         return False

   
   def save_execution_context(self, execution_start_time, execution_id: str, subscriptions: list[Subscription]):
      entity = {
         'PartitionKey': execution_id,
         'RowKey': execution_id,
         "execution_start_time": execution_start_time
      }

      self.db.insert(self.db.wara_run_history_table_name, entity)

      js = json.dumps(subscriptions, default = lambda x: x.__dict__)

      sub_entity = {
         'PartitionKey': execution_id,
         'RowKey': execution_id,
         'data': self.compress_string(js)
      }

      self.db.insert(self.db.wara_run_subscription_table_name, sub_entity)


   def compress_string(self, data: str) -> str:
      data = zlib.compress(data.encode())
      return data


   def run(self):

      try:

         if not self.config.wara_tenantId:
            Log.debug('WARA_TenantId is not set, WARA will not ignored')
            return
         
         try:
            # delete root dir
            if os.path.exists(self.exec_root_dir):
               Log.debug('WARA - deleting root folder from previous run')
               os.remove(self.exec_root_dir)
         except:
            pass

         subscriptions = self.get_subscriptions()

         if not subscriptions:
            Log.debug(f'WARA - not subscriptions found, execution ended')
            return
        
         
         execution_start_time, execution_id = self.generate_execution_id()

         Log.debug(f'WARA - executing with execution id: {execution_id}')
         
         self.db.init()

         self._create_root_exec_dir()

         self._download_scripts()

         Log.debug(f'WARA - preparing execution for subscription ids: {",".join([sub.name for sub in subscriptions])}')

         for sub in subscriptions:

            json_file_path = self._exec_collector_ps1(sub.id)

            if not json_file_path:
               raise Exception('WARA - collector.ps1 failed execution')

            excel_file_path = self.exec_analyzer_ps1(json_file_path)

            if not excel_file_path:
               raise Exception('WARA - wara_data_analyzer.ps1 failed execution')

            self.read_and_save_analyzer_excel_result(excel_file_path, sub.id, execution_id)

            if os.path.exists(json_file_path):
               os.remove(json_file_path)

            if os.path.exists(excel_file_path):
               os.remove(excel_file_path)

            Log.debug(f'WARA - execution completed for subscription id: {sub.id}')

         self.save_execution_context(execution_start_time, execution_id, subscriptions)

         Log.debug('WARA - entire execution completed successfully')

         
      except Exception as e:
         Log.exception(e)
         # if os.path.exists(self.exec_root_dir):
         #       os.remove(self.exec_root_dir)

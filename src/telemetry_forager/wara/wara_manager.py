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
import openpyxl
from win32com.client import Dispatch
import xlwings as xw
from pathlib import Path
sys.path.append(str(Path(__file__).absolute().parent))
from db import DB

class RunContext:
   def __init__(self):
      self.run_start_time = datetime.datetime.now()
      

class WARAManager:

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
      Log.debug('WARA/run - create root exec dir')
      if not os.path.exists(self.exec_root_dir):
         os.makedirs(self.exec_root_dir)

   def _del_root_exec_dir(self):
      os.rmdir(self.exec_root_dir)


   def generate_execution_id(self) -> list[datetime.datetime, str]:
      now = datetime.datetime.now()
      execution_start_time =  now
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

      Log.debug(f'WARA/run - subscription fetched successfully {result}')

      return result

   # run collector script
   def _exec_collector_ps1(self, subscription_id: str) -> str:

      '''
      returns json file path
      '''
      
      #cmd = f'pwsh -c Connect-AzAccount -Identity -TenantId {self.config.wara_tenantId} && ./1_wara_collector.ps1 -tenantid {self.config.wara_tenantId} -subscriptionids {subscription_ids}'
      cmd = f'pwsh {self.collector_script_wrapper_path} -tenantid {self.config.wara_tenantId} -subscriptionids {subscription_id}'

      Log.debug(f'WARA/run - executing collector.ps1 with cmd: {cmd}')

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
            #Log.debug(f'WARA/run - {line.rstrip()}')

         p.wait(timeout=3)

         Log.debug(f'WARA/run - finish executing collector.ps1')

      except subprocess.TimeoutExpired:
         p.kill(p.pid)
         Log.debug(f'WARA/run - finish executing collector.ps1')
      

      for file in os.listdir(self.exec_root_dir):
            if file.endswith(".json"):
               fp = os.path.join(self.exec_root_dir, file)
               Log.debug(f'WARA/run - executed collector.ps1 sucessfully, output json file {fp}')
               return fp
      
      Log.debug(f'WARA/run - collector.ps1 failed execution, no json output file found')

   # run analyzer script
   def exec_analyzer_ps1(self, json_file_path) -> str:
      '''
      returns json file file
      '''

      if not json_file_path:
         Log.exception('WARA/run - cannot find collector.ps1 json file result')
         return

      cmd = f'pwsh {self.analyzer_ps1_file_path} -JSONFile {json_file_path}'

      Log.debug(f'WARA/run - executing wara_data_analyzer.ps1 with cmd: {cmd}')

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
            #Log.debug(f'WARA/run - {line.rstrip()}') #reduce logging

         p.wait(timeout=3)
         
         Log.debug(f'WARA/run - finish executing wara_data_analyzer.ps1')

      except subprocess.TimeoutExpired:
         p.kill(p.pid)
         Log.debug(f'WARA/run - finish executing wara_data_analyzer.ps1')

      
      xlsx_file_path = None
      for file in os.listdir(self.exec_root_dir):
            if file.endswith(".xlsx"):
               xlsx_file_path = os.path.join(self.exec_root_dir, file)
               break
               # refresh Excel to fix Pandas read cell with formula null
               # https://stackoverflow.com/questions/40893870/refresh-excel-external-data-with-python
               # https://stackoverflow.com/questions/36116162/python-openpyxl-data-only-true-returning-none
               
      
      if not xlsx_file_path:
         Log.debug(f'WARA/run - wara_data_analyzer.ps1 failed execution, no Excel output file found')
         return

      # requires Excel installed on Windows container, exploring.
      self.refresh_xlsx(xlsx_file_path)
      
      Log.debug(f'WARA/run - executed wara_data_analyzer.ps1 sucessfully, output Excel file. {xlsx_file_path}')

      return xlsx_file_path
      

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
            Log.exception('WARA/run - cannot find analyzer.ps1 Excel file result')
            return False
         
         r_ok, r_err = self.read_and_save_recommendations_json(excel_file_path, execution_id, subscription_id)

         if not r_ok:
            Log.exception(f'WARA/run - error reading Excel Recommendation worksheet. {r_err}')

         i_ok, i_err = self.read_impacted_resources_json(subscription_id, execution_id, excel_file_path)

         if not i_ok:
            Log.exception(f'WARA/run - error reading Excel Impacted Resources worksheet. {i_err}')


         rt_ok, rt_err = self.read_resource_types_json(subscription_id, execution_id, excel_file_path)

         if not rt_ok:
            Log.exception(f'WARA/run - error reading Excel Resource Type worksheet. {rt_err}')

         ret_ok, ret_err = self.read_retirements_json(subscription_id, execution_id, excel_file_path)

         if not ret_ok:
            Log.exception(f'WARA/run - error reading Excel Retirement worksheet. {ret_err}')
      

      except Exception as e:
         return False

   
   def save_execution_context(self, execution_start_time, execution_id: str, subscriptions: list[Subscription]):

      def row_key(dt):
         t = (datetime.datetime(9999, 12, 31, 23, 59, 59, 999999) - dt).total_seconds() * 10000000
         return f'{t:.0f}'

      # Store the entities using a RowKey that naturally sorts in reverse date/time order by using
      # the most recent entry is always the first one in the table.
      # https://learn.microsoft.com/en-us/azure/storage/tables/table-storage-design-patterns#log-tail-pattern
      entity = {
         'PartitionKey': execution_id,
         'RowKey': row_key(execution_start_time),
         'execution_start_time': execution_start_time,
         'display_execution_start_time': execution_start_time.strftime("%a %d %b %Y %H:%M:%S")
      }

      self.db.insert(self.db.wara_run_history_table_name, entity)

      js = json.dumps(subscriptions, default = lambda x: x.__dict__)

      sub_entity = {
         'PartitionKey': execution_id,
         'RowKey': execution_id,
         'data': self.compress_string(js)
      }

      self.db.insert(self.db.wara_run_subscription_table_name, sub_entity)


   def save_subscriptions(self, subscriptions: list[Subscription]):
      pass

   def save_run_history(self, execution_start_time: datetime.datetime, execution_id: str):

      def row_key(dt):
         t = (datetime.datetime(9999, 12, 31, 23, 59, 59, 999999) - dt).total_seconds() * 10000000
         return f'{t:.0f}'

      # Store the entities using a RowKey that naturally sorts in reverse date/time order by using
      # the most recent entry is always the first one in the table.
      # https://learn.microsoft.com/en-us/azure/storage/tables/table-storage-design-patterns#log-tail-pattern
      entity = {
         'PartitionKey': execution_id,
         'RowKey': row_key(execution_start_time),
         'execution_start_time': execution_start_time,
         'display_execution_start_time': execution_start_time.strftime("%a %d %b %Y %H:%M:%S")
      }

      self.db.insert(self.db.wara_run_history_table_name, entity)



   def compress_string(self, data: str) -> str:
      data = zlib.compress(data.encode())
      return data


   def run(self):

      try:

         if not self.config.wara_tenantId:
            Log.debug('WARA/run - TenantId is not set, WARA will not ignored')
            return
         
         try:
            # delete root dir
            if os.path.exists(self.exec_root_dir):
               Log.debug('WARA/run - deleting root folder from previous run')
               os.remove(self.exec_root_dir)
         except:
            pass

         subscriptions = self.get_subscriptions()

         if not subscriptions:
            Log.debug(f'WARA/run - not subscriptions found, execution ended')
            return
        
         
         execution_start_time, execution_id = self.generate_execution_id()

         Log.debug(f'WARA/run - executing with execution id: {execution_id}')
         
         self.db.init()

         self._create_root_exec_dir()

         self._download_scripts()

         Log.debug(f'WARA/run - preparing execution for subscription ids: {",".join([sub.name for sub in subscriptions])}')

         for sub in subscriptions:

            json_file_path = self._exec_collector_ps1(sub.id)

            if not json_file_path:
               raise Exception('WARA/run - collector.ps1 failed execution')

            excel_file_path = self.exec_analyzer_ps1(json_file_path)

            if not excel_file_path:
               raise Exception('WARA/run - wara_data_analyzer.ps1 failed execution')

            Log.debug(f'WARA/run - processing data of Excel file {excel_file_path}')

            self.read_and_save_analyzer_excel_result(excel_file_path, sub.id, execution_id)

            Log.debug(f'WARA/run - process data of Excel file completed successfully')

            if os.path.exists(json_file_path):
               os.remove(json_file_path)

            if os.path.exists(excel_file_path):
               os.remove(excel_file_path)

            Log.debug(f'WARA/run - execution completed for subscription id: {sub.id}')

         self.save_execution_context(execution_start_time, execution_id, subscriptions)

         Log.debug('WARA/run - entire execution completed successfully')

         
      except Exception as e:
         Log.exception(f'WARA/run - {str(e)}')


   def delete_run_history(self, days_to_keep):
      
      try:

         exec_ids_to_del = []
         datetime_to_start_del = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)
         datetime_to_start_del = datetime_to_start_del.strftime("%Y-%m-%dT%H:%M:%S")

         filter = f"execution_start_time lt datetime'{str(datetime_to_start_del)}'"
         
         run_history_to_del = self.db.query_entities(self.db.wara_run_history_table_name, filter)

         for entity in run_history_to_del:
            exec_ids_to_del.append((entity['PartitionKey'], entity['RowKey']))

         if not exec_ids_to_del:
            Log.debug(f'WARA/delete_run_history - no run history to delete. days to keep = {days_to_keep}. Date/time to start delete {datetime_to_start_del}')
            return
         

         for partitionkey, rowkey in exec_ids_to_del:

            execid = partitionkey

            recommendations = self.db.query_entities(self.db.wara_recommendation_table_name, f"RowKey eq '{execid}'")
            for rec in recommendations:
               self.db.delete_by_entity(self.db.wara_recommendation_table_name, rec)

            impacted_resources = self.db.query_entities(self.db.wara_impacted_resources_table_name, f"RowKey eq '{execid}'")
            for ir in impacted_resources:
               self.db.delete_by_entity(self.db.wara_impacted_resources_table_name, ir)

            resource_types = self.db.query_entities(self.db.wara_resource_type_table_name, f"RowKey eq '{execid}'")
            for rt in resource_types:
               self.db.delete_by_entity(self.db.wara_resource_type_table_name, rt)

            retirements = self.db.query_entities(self.db.wara_retirements_table_name, f"RowKey eq '{execid}'")
            for r in retirements:
               self.db.delete_by_entity(self.db.wara_retirements_table_name, r)


            self.db.delete_row(self.db.wara_run_subscription_table_name, execid, execid)

            self.db.delete_row(self.db.wara_run_history_table_name, execid, rowkey)

      except Exception as e:
         Log.exception(f'WARA/delete_run_history - {str(e)}')


   def refresh_xlsx(self, xlsx_file_path):
      
      Log.debug(f'WARA/run - refreshing xlsx file {xlsx_file_path}')

      import win32com.client

      # # Start an instance of Excel
      # xlapp = win32com.client.DispatchEx("Excel.Application")

      # # Open the workbook in said instance of Excel
      # wb = xlapp.workbooks.open(xlsx_file_path)

      # # Optional, e.g. if you want to debug
      # # xlapp.Visible = True

      # # Refresh all data connections.
      # wb.RefreshAll()
      # wb.Save()

      # # Quit
      # xlapp.Quit()

      app_excel = xw.App(visible = False)

      wbk = xw.Book(xlsx_file_path)
      wbk.api.RefreshAll()

      # two options to save
      wbk.save(xlsx_file_path) # this will overwrite the file

      app_excel.kill()
      del app_excel

      Log.debug(f'WARA/run - refresh xlsx file successfully')



      
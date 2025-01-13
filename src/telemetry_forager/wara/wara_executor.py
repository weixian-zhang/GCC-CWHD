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


   def generate_execution_id(self):
      return datetime.datetime.now().strftime('%Y%m%d%H%M%S')
   
   # download scripts
   # 1_wara_collector.ps1
   # 2_wara_data_analyzer.ps1
   # 3_wara_reports_generator.ps1
   def _download_scripts(self):
      urllib.request.urlretrieve(self.collector_ps1_url, self.collector_ps1_file_path )
      urllib.request.urlretrieve(self.analyzer_ps1_url, self.analyzer_ps1_file_path)
      urllib.request.urlretrieve(self.wara_report_generator_ps1_url, self.wara_report_generator_ps1_file_path)


   # get subscription ids
   def _get_subscription_ids(self):
      if self.config.wara_subsciptionIds:
         subids = ','.join(self.config.wara_subsciptionIds)
         Log.debug(f'WARA - subscription ids in envar {subids}')
         return self.config.wara_subsciptionIds
         #return ','.join(self.config.wara_subsciptionIds)
      
      client = SubscriptionClient(DefaultAzureCredential())
      subscription_list  = client.subscriptions.list()
      subscription_ids = [sub.subscription_id for sub in subscription_list]
      #result = ','.join(subscription_ids)

      subids = ','.join(self.config.wara_subsciptionIds)
      Log.debug(f'WARA - subscription ids fetched from API {subids}')

      return subscription_ids

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
      

      p_out, p_err = p.communicate()

      Log.debug(f'WARA - {p_out}')

      if p_err:
         Log.exception(p_err)
         return

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

      # def _get_collector_json_result_file_name():
      #    for file in os.listdir(self.exec_root_dir):
      #       if file.endswith(".json"):
      #          return file
      #    return ''
      
      # json_file_name = _get_collector_json_result_file_name()

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

      p_out, p_err = p.communicate()

      Log.debug(f'WARA - {p_out}')

      if p_err:
         Log.exception(p_err)
         return
      
      for file in os.listdir(self.exec_root_dir):
            if file.endswith(".xlsx"):
               fp = os.path.join(self.exec_root_dir, file)
               Log.debug(f'WARA - executed wara_data_analyzer.ps1 sucessfully, output Excel file. {fp}')
               return fp
     
      Log.debug(f'WARA - wara_data_analyzer.ps1 failed execution, no Excel output file found')

   def read_and_save_recommendations_json(self, file_path: str, execution_id, subscription_id) -> bool:
         try:
            
            df = pd.read_excel(file_path, 'Recommendations')

            # drop unused columns: 
               # Azure Service / Well-Architected
               # Recommendation Source
               # Add associated Outage TrackingID and/or Support Request # and/or Service Retirement TrackingID 
               # Observation / Annotation
               # Recommendation Id
            cols = [2,3,11,12,13]
            df.drop(df.columns[cols],axis=1,inplace=True)

            json = df.to_json(orient='records')

            compessed_recomm_json = self.compress_string(json)

            recomm_entity = {
               'PartitionKey': execution_id,
               'RowKey': subscription_id,
               'data': compessed_recomm_json
            }

            self.db.insert(self.db.recommendation_table_name, recomm_entity)

            return True
            
         except Exception as e:
            Log.exception(e)
            return False
      
   def read_impacted_resources_json(self, file_path: str) -> str:
      try:
         df = pd.read_excel(file_path, 'ImpactedResources')

         # drop unused columns: 
            # How was the resource/recommendation validated or what actions need to be taken?
            # recommendationId
            # supportTicketId
            # source
            # WAF Pillar
            # checkName

         cols = [0,3,15,16,17,18]
         df.drop(df.columns[cols],axis=1,inplace=True)

         return df.to_json(orient='records')
      except Exception as e:
         Log.exception(e)

   def read_resource_types_json(self, file_path: str) -> str:
      try:
         df = pd.read_excel(file_path, 'ResourceTypes')

         # drop unused columns: 
            # Available in APRL/ADVISOR?
            # Assessment Owner
            # Status
            # Notes

         cols = [2,3,4,5]
         df.drop(df.columns[cols],axis=1,inplace=True)
         
         return df.to_json(orient='records')
      
      except Exception as e:
         Log.exception(e)

   def read_retirements_json(self, file_path: str) -> str:
      try:
         df = pd.read_excel(file_path, 'Retirements')
         return df.to_json(orient='records')
      except Exception as e:
         Log.exception(e)

   # pandas read excel from Excel
   def read_and_save_analyzer_excel_result(self, excel_file_path, subscription_id: str, execution_id: str):

      # def _get_analyzer_excel_result_file_name():
      #    for file in os.listdir(self.exec_root_dir):
      #       if file.endswith(".xlsx"):
      #          return file
      #    return ''

      # excel_file_name = _get_analyzer_excel_result_file_name()

      if not excel_file_path:
         Log.exception('WARA - cannot find analyzer.ps1 Excel file result')
         return
      
      #excel_file_path = os.path.join(self.exec_root_dir, excel_file_name)

      r_ok = self.read_and_save_recommendations_json(excel_file_path)

      if not r_ok:
         return

   
   def save_execution_context(self, execution_id: str, subscription_ids: list[str]):
      entity = {
         'PartitionKey': execution_id,
         'RowKey': execution_id,
         'subscription_ids': ','.join(subscription_ids),
      }

      self.db.insert(self.db.run_history_table_name, entity)


   def compress_string(self, data: str) -> str:
      data = zlib.compress(data.encode())
      return data

   def decompress_string(self, data: str) -> str:
      data = zlib.decompress(data).decode()
      return data

   # save data to table storage for Grafana query

   # zip and upload
      # Excel action plan
      # executive ppt
      # assessment report word doc

   # FastAPI - endpoints
      # run WARA script anytime
      # 

   # delete root exec dir


   def run(self):

      try:

         if not self.config.wara_tenantId:
            Log.debug('WARA_TenantId is not set, WARA will not ignored')
            return
         
         execution_id = self.generate_execution_id()

         Log.debug(f'WARA in running with execution id: {execution_id}')
         
         self.db.init()

         self._create_root_exec_dir()

         self._download_scripts()

         subscription_ids = self._get_subscription_ids()

         for sub_id in subscription_ids:


            # get resource groups for each subscritpion
            # wara report will generate for each resource group level by default
            # in this way, we can filter recommendations and impacted resource by subscription id and resource group
            # # table storage partition key is {subid + resource group id}
            # table storage row key is {run_start_time_epoch}
            # **to reconsider becoz multiple runs at resource group may cause unreliability. And error at any resource group causes
            # whole report at subscription level to fail.

            # json_file_path = self._exec_collector_ps1(sub_id)

            # if not json_file_path:
            #    raise Exception('WARA - collector.ps1 failed execution')

            # excel_file_path = self.exec_analyzer_ps1(json_file_path)

            # if not excel_file_path:
            #    raise Exception('WARA - wara_data_analyzer.ps1 failed execution')

            #self.read_and_save_analyzer_excel_result(excel_file_path, sub_id, execution_id)
            self.read_and_save_analyzer_excel_result('C:\\Weixian\\projects\\VBD\\GCC-CWHD\\src\\telemetry_forager\\wara\\temp_wara_exec\\WARA Action Plan 2025-01-13-21-29.xlsx',
                                                     sub_id, execution_id)

            # if os.path.exists(json_file_path):
            #    os.remove(json_file_path)

            # if os.path.exists(excel_file_path):
            #    os.remove(excel_file_path)

            Log.debug(f'WARA - {execution_id}run completed')

         self.save_execution_context(execution_id, subscription_ids)

      except Exception as e:
         Log.exception(e)
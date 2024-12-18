import subprocess
import os
import log as Log
import urllib.request
import datetime
from config import AppConfig
from azure.identity import DefaultAzureCredential
from azure.mgmt.subscription import SubscriptionClient
import pandas as pd
class RunContext:
   def __init__(self):
      self.run_start_time = datetime.datetime.now()
      

class WARAActionPlanner:

   def __init__(self, config: AppConfig):
      file_full_path = os.path.realpath(__file__)
      cwd = os.path.dirname(file_full_path)

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
         Log.debug(f'WARA - subscription ids in envar {self.config.wara_subsciptionIds}')
         return ','.join(self.config.wara_subsciptionIds)
      
      client = SubscriptionClient(DefaultAzureCredential())
      subscription_list  = client.subscriptions.list()
      subscription_ids = [sub.subscription_id for sub in subscription_list]
      result = ','.join(subscription_ids)
   
      Log.debug(f'WARA - subscription ids fetched from API {result}')

      return result

   # run collector script
   def _exec_collector_ps1(self, subscription_ids: str):

      #cmd = f'pwsh -c Connect-AzAccount -Identity -TenantId {self.config.wara_tenantId} && ./1_wara_collector.ps1 -tenantid {self.config.wara_tenantId} -subscriptionids {subscription_ids}'
      cmd = f'pwsh {self.collector_script_wrapper_path} -tenantid {self.config.wara_tenantId} -subscriptionids {subscription_ids}'

      Log.debug(f'WARA - executing collector.ps1 with cmd: {cmd}')

      p = subprocess.Popen(cmd, 
                           shell=True,
                           text=True,
                           stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
      

      p_out, p_err = p.communicate()

      if p_err:
         Log.exception(p_err)
         return

      Log.debug(f'WARA - executed connector.ps1 sucessfully. {p_out}')

   # run analyzer script
   def _exec_analyzer_ps1(self):


      def _get_collector_json_result_file_name():
         for file in os.listdir(self.exec_root_dir):
            if file.endswith(".json"):
               return file
         return ''
      
      json_file_name = _get_collector_json_result_file_name()

      if not json_file_name:
         Log.exception('WARA - cannot find collector.ps1 json file result')
         return

      cmd = f'pwsh {self.analyzer_ps1_file_path} -JSONFile {json_file_name}'

      Log.debug(f'WARA - executing data_analyzer.ps1 with cmd: {cmd}')

      p = subprocess.Popen(cmd, 
                           shell=True,
                           text=True,
                           stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)

      p_out, p_err = p.communicate()

      if p_err:
         Log.exception(p_err)
         return

      Log.debug(f'WARA - executed connector.ps1 sucessfully. {p_out}')

   # pandas read excel from Excel
   def _load_analyzer_excel_result(self):

      def _get_analyzer_excel_result_file_name():
         for file in os.listdir(self.exec_root_dir):
            if file.endswith(".xlsx"):
               return file
         return ''

      excel_file_name = _get_analyzer_excel_result_file_name()

      if not excel_file_name:
         Log.exception('WARA - cannot find analyzer.ps1 Excel file result')
         return
      
      excel_file_path = os.path.join(self.exec_root_dir, excel_file_name)

      df_recommendations = pd.read_excel(excel_file_path, 'Recommendations')

      df_impacted_resources = pd.read_excel(excel_file_path, 'ImpactedResources')

      df_resource_type = pd.read_excel(excel_file_path, 'ResourceTypes')

      df_retirements = pd.read_excel(excel_file_path, 'Retirements')

      pass


   # save data to table storage for Grafana query

   # zip and upload
      # Excel action plan
      # executive ppt
      # assessment report word doc

   # FastAPI - endpoints
      # run WARA script anytime
      # 

   # delete root exec dir


   def run_wara(self):

      try:

         if not self.config.wara_tenantId:
            Log.debug('WARA_TenantId is not set, WARA will not ignored')
            return

         self._create_root_exec_dir()

         self._download_scripts()

         subscription_ids = self._get_subscription_ids()

         #self._exec_collector_ps1(subscription_ids)

         # self._exec_analyzer_ps1()

         self._load_analyzer_excel_result()

         Log.debug('WARA - run completed')

      except Exception as e:
         Log.exception(e)
import subprocess
import os
import log as Log
import urllib.request
import datetime
from config import AppConfig
from azure.identity import DefaultAzureCredential
from azure.mgmt.subscription import SubscriptionClient
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
      self.wrapper_ps1_path = os.path.join(cwd, 'wara_script_wrapper.ps1')
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

      # append azure authn to collector script.
      # f = open(self.collector_ps1_file_path, 'r')
      # collector_script_content = f.read()
      # f.close()

      # code_prepend = f'''
      # Connect-AzAccount -TenantId {self.config.wara_tenantId} \n
      # '''

      # code_prepend += collector_script_content

      # f = open(self.collector_ps1_file_path, 'w')
      # f.write(code_prepend)
      # f.close()

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
      cmd = f'pwsh {self.wrapper_ps1_path} -tenantid {self.config.wara_tenantId} -subscriptionids {subscription_ids}'

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

      # p_out, p_err = p.communicate(cmd2)
      
      Log.debug(f'WARA - executed connector.ps1 sucessfully. {p_out}')

      # for file in os.listdir(self.exec_root_dir):
      #    if file.endswith(".json"):
      #       f = open(os.path.join(self.exec_root_dir, file), 'r')
      #       print(f.read())

      #p_out, p_err = p.communicate()

      # print(p_out.decode('utf-8'))

      # if p_err:
      #    Log.exception(p_err)

   # run analyzer script

   # pandas read excel from Excel

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

         self._exec_collector_ps1(subscription_ids)

         #print(p_out.decode('utf-8'))

      except Exception as e:
         Log.exception(e)
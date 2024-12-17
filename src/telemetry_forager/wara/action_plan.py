import subprocess
import os
import log as Log
import urllib.request
import datetime

class RunContext:
   def __init__(self):
      self.run_start_time = datetime.datetime.now()
      

class WARAActionPlanner:

   def __init__(self):
      file_full_path = os.path.realpath(__file__)
      cwd = os.path.dirname(file_full_path)

      self.exec_root_dir = os.path.join(cwd, 'temp_wara_exec') #, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
      self.collector_ps1_url = 'https://github.com/Azure/Azure-Proactive-Resiliency-Library-v2/raw/refs/heads/main/tools/1_wara_collector.ps1'
      self.analyzer_ps1_url = 'https://raw.githubusercontent.com/Azure/Azure-Proactive-Resiliency-Library-v2/refs/heads/main/tools/2_wara_data_analyzer.ps1'
      self.wara_report_generator_ps1_url = 'https://raw.githubusercontent.com/Azure/Azure-Proactive-Resiliency-Library-v2/refs/heads/main/tools/3_wara_reports_generator.ps1'
      self.collector_ps1_file_name = '1_wara_collector.ps1'
      self.analyzer_ps1_file_name = '2_wara_data_analyzer.ps1'
      self.wara_report_generator_ps1_file_name = '3_wara_reports_generator.ps1'
      

   # create temp folder for execution. All execution files will be stored here.
   def _create_root_exec_dir(self):
      if not os.path.exists(self.exec_root_dir):
         os.makedirs(self.exec_root_dir)

   def _del_root_exec_dir(self):
      os.rmdir(self.exec_root_dir)

   # download scripts
   # 1_wara_collector.ps1
   # 2_wara_data_analyzer.ps1
   # 3_wara_reports_generator.ps1
   def _download_scripts(self):
      urllib.request.urlretrieve(self.collector_ps1_url, os.path.join(self.exec_root_dir, self.collector_ps1_file_name))
      urllib.request.urlretrieve(self.analyzer_ps1_file_name, os.path.join(self.exec_root_dir, self.analyzer_ps1_file_name))
      urllib.request.urlretrieve(self.wara_report_generator_ps1_file_name, os.path.join(self.exec_root_dir, self.wara_report_generator_ps1_file_name))

   # run collector script

   # run analyzer script

   # pandas read excel from analyzer script

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

         self._create_root_exec_dir()

         self._download_scripts()

         # p = subprocess.Popen(f'''pwsh wara_pwsh_script"
         #                      ''', stdout=subprocess.PIPE)
         # p_out, p_err = p.communicate()

         # if not p_err:
         #    Log.exception(p_err)

         #print(p_out.decode('utf-8'))

      except Exception as e:
         Log.exception(e)
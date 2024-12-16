import subprocess
import os
import log as Log

file_full_path = os.path.realpath(__file__)
cwd = os.path.dirname(file_full_path)
wara_pwsh_script = 'tesy.ps1'

def run_wara_pwsh():
   try:
      p = subprocess.Popen(f'''pwsh wara_pwsh_script"
                           ''', stdout=subprocess.PIPE)
      p_out, p_err = p.communicate()

      if not p_err:
         Log.exception(p_err)

      print(p_out.decode('utf-8'))

   except Exception as e:
      Log.exception(e)
import subprocess, sys
import os

file_full_path = os.path.realpath(__file__)
cwd = os.path.dirname(file_full_path)

def run_pwsh():
   p = subprocess.Popen(f'''pwsh -c {os.path.join(cwd, 'testy.ps1')}"
                        ''', stdout=subprocess.PIPE)
   p_out, p_err = p.communicate()

   print(p_out.decode('utf-8'))
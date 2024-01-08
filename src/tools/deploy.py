

import os
from pathlib import Path
from zipfile import ZipFile
import subprocess

func_zip_name = 'func-app.zip'
az_resource_group = 'rg-lta-cwhd'
az_func_name = 'func-lta-cwhd'

current_working_directory = os.path.join(Path(os.getcwd()).parent.parent.absolute())
azfunc_directory = os.path.join(current_working_directory,'src', 'az_function')
deployment_directory = os.path.join(current_working_directory, 'deploy')
deployment_file_path = os.path.join(current_working_directory, 'deploy', func_zip_name)
func_deploy_cmd = f'az functionapp deployment source config-zip -g {az_resource_group} -n {az_func_name} --build-remote --src "func-app.zip"'

files_to_zip = ['requirements.txt', 'host.json', 'local.settings.json']

os.chdir(azfunc_directory)

for file in os.listdir(azfunc_directory):
    if file.endswith('.py'):
        files_to_zip.append(file)

print(f'detected source files {files_to_zip}')

print(f'creating zip file {func_zip_name}')

zipObj = ZipFile(deployment_file_path, 'w')
                 
for f in files_to_zip:
    zipObj.write(f)

zipObj.close()

print(f'finish creating zip file at {deployment_file_path}')

os.chdir(deployment_directory)

print(f'executing function deployment az cli cmd {func_deploy_cmd}')

p = subprocess.Popen(func_deploy_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
for line in p.stdout.readlines():
    print(line),
retval = p.wait()
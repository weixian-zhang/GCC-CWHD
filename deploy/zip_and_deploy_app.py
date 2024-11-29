

import os
from pathlib import Path
from zipfile import ZipFile
import subprocess
from sys import gettrace

zip_file_name = 'cwhd.zip'
resource_group = 'appsvc-cwhd-1_group'
app_service_name = 'appsvc-cwhd-1'


# root directory of the project, if not in debug mode, go up two directory levels
current_working_directory = os.path.join(Path(os.getcwd()).absolute()) if gettrace() else os.path.join(Path(os.getcwd()).parent.absolute())

telemetry_forager_directory = os.path.join(current_working_directory,'src', 'telemetry_forager')
deployment_directory = os.path.join(current_working_directory, 'deploy')
deploy_to_file_path = os.path.join(deployment_directory, zip_file_name)
azcli_deploy_cmd = f'az webapp deploy  --resource-group {resource_group} --name {app_service_name} --src-path {zip_file_name}'


files_to_zip = ['requirements.txt']

os.chdir(telemetry_forager_directory)

# get all python files to zip
for file in os.listdir(telemetry_forager_directory):
    if file.endswith('.py'):
        files_to_zip.append(file)

print(f'detected source files {files_to_zip}')

print(f'creating zip file {zip_file_name}')

zipObj = ZipFile(deploy_to_file_path, 'w')
                 
for f in files_to_zip:
    zipObj.write(f)

zipObj.close()

print(f'finish creating zip file at {deploy_to_file_path}')

os.chdir(deployment_directory)

print(f'executing {azcli_deploy_cmd}')

p = subprocess.Popen(azcli_deploy_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
for line in p.stdout.readlines():
    print(line),
retval = p.wait()

print(f'finish executing: {azcli_deploy_cmd}')
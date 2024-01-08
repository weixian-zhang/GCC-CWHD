

import os
from pathlib import Path

current_working_directory = os.getcwd()
azfunc_directory = os.path.join(Path(current_working_directory).parent.absolute(), 'GCC-CWHD', 'src', 'az_function')

files_to_zip = ['requirements.txt', 'host.json', 'local.settings.json']

os.chdir(azfunc_directory)

for file in os.listdir(azfunc_directory):
    if file.endswith('.py'):
        files_to_zip.append(file)


print(files_to_zip)
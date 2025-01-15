# Build stage
# FROM mcr.microsoft.com/windows/servercore:ltsc2022 AS builder
FROM mcr.microsoft.com/windows/servercore:ltsc2022

# Set shell to PowerShell
SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]

# Download and install Python 3.12
# RUN Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.12.2/python-3.12.2-amd64.exe -OutFile python-installer.exe ; \
#     Start-Process python-installer.exe -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1' -Wait ; \
#     Remove-Item python-installer.exe

# Install pip and any build dependencies
# RUN python -m pip install --upgrade pip

#RUN python -m pip install -r requirements.txt:

# Runtime stage
#FROM mcr.microsoft.com/windows/servercore:ltsc2022

# Copy Python installation from builder stage
# COPY --from=builder C:/Python312 C:/Python312

# # # Copy PowerShell Core installation from builder stage
# COPY --from=builder C:/Program C:/Program 
# COPY --from=builder Files/PowerShell Files/PowerShell

# Download and install PowerShell Core
# RUN Invoke-WebRequest -Uri https://github.com/PowerShell/PowerShell/releases/download/v7.3.4/PowerShell-7.3.4-win-x64.msi -OutFile powershell-installer.msi ; \
#     Start-Process msiexec.exe -ArgumentList '/i powershell-installer.msi /quiet ADD_EXPLORER_CONTEXT_MENU_OPENPOWERSHELL=1 ENABLE_PSREMOTING=1 REGISTER_MANIFEST=1' -Wait ; \
#     Remove-Item powershell-installer.msi

# Set Python and PowerShell paths
#RUN setx /M PATH $($Env:PATH + ';C:\Python312;C:\Python312\Scripts;C:\Program Files\PowerShell')

# Set shell to PowerShell
#SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]

# install chocolatey
RUN Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

#install git
# RUN choco install git -y
RUN choco install git.install -y
RUN git config --global core.autocrlf true

# install python 3.11
RUN choco install python311 -y
RUN python -m pip install --upgrade pip

# install powershell core
RUN choco install powershell-core --version=7.4.2 -y

# install WARA required Powershell modules
RUN pwsh -c Install-Module -Name ImportExcel -Force -SkipPublisherCheck
RUN pwsh -c Install-Module -Name Az.ResourceGraph -Force -SkipPublisherCheck
RUN pwsh -c Install-Module -Name Az.Accounts -Force -SkipPublisherCheck
RUN pwsh -c Install-Module -Name powershell-yaml -Force -SkipPublisherCheck

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Install dependencies in a temporary directory
# RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
RUN pip install --no-cache-dir -r requirements.txt 


# Expose the port FastAPI will run on
EXPOSE 8000 

# Run FastAPI with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


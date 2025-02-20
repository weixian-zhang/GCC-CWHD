# Build stage
# FROM mcr.microsoft.com/windows/servercore:ltsc2022 AS builder
FROM mcr.microsoft.com/windows/servercore:ltsc2022

# Set shell to PowerShell
SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]

# install chocolatey
RUN Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

#install git
# RUN choco install git -y
RUN choco install git.install -y
RUN git config --global core.autocrlf true

# install python 3.11
RUN choco install python311 -y
RUN python.exe -m pip install --upgrade pip

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Install dependencies in a temporary directory
#RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
RUN pip install --no-cache-dir -r requirements.txt 


# install powershell core
RUN choco install powershell-core --version=7.4.5 -y

# install WARA required Powershell modules
RUN pwsh -c Install-Module -Name ImportExcel -Force -SkipPublisherCheck
RUN pwsh -c Install-Module -Name Az.ResourceGraph -Force -SkipPublisherCheck
RUN pwsh -c Install-Module -Name Az.Accounts -Force -SkipPublisherCheck
RUN pwsh -c Install-Module -Name powershell-yaml -Force -SkipPublisherCheck


# Expose the port FastAPI will run on
EXPOSE 8000 

# Run FastAPI with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


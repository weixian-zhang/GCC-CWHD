# Build stage
# FROM mcr.microsoft.com/windows/servercore:ltsc2022 AS builder
# FROM mcr.microsoft.com/windows/servercore:ltsc2022
FROM mcr.microsoft.com/windows/server:ltsc2022

# office setup
WORKDIR C:\\odtsetup

ADD https://download.microsoft.com/download/2/7/A/27AF1BE6-DD20-4CB4-B154-EBAB8A7D4A7E/officedeploymenttool_17830-20162.exe odtsetup.exe

RUN odtsetup.exe /quiet /norestart /extract:C:\\odtsetup

# Copy configuration file 
ADD wara/msoffice-configuration.xml .

RUN setup.exe /download C:\\odtsetup\\msoffice-configuration.xml

RUN setup.exe /configure C:\\odtsetup\\msoffice-configuration.xml

WORKDIR /

# Remove installation directroy after install
RUN rmdir /s /q C:\\odtsetup

# Create the Desktop directory required for Office 365 to function
RUN mkdir C:\\Windows\\SysWOW64\\config\\systemprofile\\Desktop

VOLUME C:\\data


# # Set shell to PowerShell
SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'Continue'; $verbosePreference='Continue';"]


# install and configure chocolatey
RUN Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
RUN choco feature enable --name allowGlobalConfirmation

# install powershell core
RUN choco install powershell-core --version 7.4.5 --force


# install WARA required Powershell modules
RUN pwsh -c Install-Module -Name ImportExcel -Force -SkipPublisherCheck
RUN pwsh -c Install-Module -Name Az.ResourceGraph -Force -SkipPublisherCheck
RUN pwsh -c Install-Module -Name Az.Accounts -Force -SkipPublisherCheck
RUN pwsh -c Install-Module -Name powershell-yaml -Force -SkipPublisherCheck


#install git
RUN choco install git -y
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


# Expose the port FastAPI will run on
EXPOSE 8000 

# Run FastAPI with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


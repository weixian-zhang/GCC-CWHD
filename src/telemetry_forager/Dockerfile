# --- Stage 1: Build Stage ---
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Copy only requirements to install dependencies
COPY requirements.txt .

# Install dependencies in a temporary directory
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# --- Stage 2: Runtime Stage ---
FROM python:3.11-slim

ENV HealthStatusThreshold='{     "metricUsageThreshold": {         "vm": {             "cpuUsagePercentage": 80,             "memoryUsagePercentage": 80,             "diskUsagePercentage": 80         }     } }'
ENV APPLICATIONINSIGHTS_CONNECTION_STRING=''
ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1


# Set working directory
WORKDIR /app

# Copy dependencies from the builder stage
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

RUN rm -rf /var/lib/apt/lists/*

# Update the list of packages
RUN apt-get update

# Install pre-requisite packages.
RUN apt-get install -y wget

# install git
RUN apt-get install git -y
RUN git --version

# Download the PowerShell package file
RUN wget https://github.com/PowerShell/PowerShell/releases/download/v7.2.24/powershell_7.2.24-1.deb_amd64.deb

###################################
# Install the PowerShell package
RUN dpkg -i powershell_7.2.24-1.deb_amd64.deb || true

RUN pwsh -c Install-Module -Name ImportExcel -Force -SkipPublisherCheck
RUN pwsh -c Install-Module -Name Az.ResourceGraph -Force -SkipPublisherCheck
RUN pwsh -c Install-Module -Name Az.Accounts -Force -SkipPublisherCheck

# authn SPN
# https://www.techtarget.com/searchwindowsserver/tutorial/Using-PowerShell-for-Azure-service-principal-authentication
# docker powershell command for debian
# https://github.com/PowerShell/PowerShell-Docker/blob/44a656a80ea5f72bcba5de3fc31c9617ef0bd674/release/7-3/debian11/docker/Dockerfile

# RUN pwsh -c " \
# \$clientId = ''; \
# \$clientSecret = '' | ConvertTo-SecureString -AsPlainText -Force; \
# \$credential = [PSCredential]::New(\$clientId,\$clientSecret); \
# Connect-AzAccount -ServicePrincipal -Credential \$credential -Tenant ''; \
# get-azcontext; \
# "

# Expose the port FastAPI will run on
EXPOSE 8000

# Run FastAPI with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

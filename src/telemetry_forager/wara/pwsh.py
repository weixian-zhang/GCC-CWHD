import subprocess, sys


p = subprocess.Popen('''pwsh -c "
                        $clientId = ''; \
                        $clientSecret = '' | ConvertTo-SecureString -AsPlainText -Force; \
                        $credential = [PSCredential]::New($clientId,$clientSecret); \
                        Connect-AzAccount -ServicePrincipal -Credential \$credential -Tenant ''; \
                        get-azcontext; \
                     ''', 
                     stdout=sys.stdout)
p.communicate()
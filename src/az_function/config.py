import json
import os
from logging import Logger

# standardTestName applies to App Service resource type only
class ResourceParameter:
    def __init__(self, resourceId, subscriptionId,standardTestName='' ) -> None:
        self.resourceId = resourceId
        self.subscriptionId = subscriptionId
        self.standardTestName = standardTestName

class AppConfig:
    def __init__(self) -> None:
        self.workspaceID = ''
        self.appServiceAppInsightStandardTestMap = {}
        self.loaded = False

    def load_from_envar(self):
        if self.loaded:
            return
        
        self.workspaceID = os.environ.get('WorkspaceID')

        if not self.workspaceID: # or not mapJson:
            raise Exception('necessary environment variables not found')

        self.loaded = True

    def get_standardTestName_by_appsvc_rscId(self, appsvcRscId: str):
        appsvcRscId = appsvcRscId if appsvcRscId[0] != '/' else ''.join(appsvcRscId[1:])
        return self.appServiceAppInsightStandardTestMap[appsvcRscId]
        

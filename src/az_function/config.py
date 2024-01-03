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
        map = os.environ.get('AppServiceAppInsightStandardTestMap')
        mapJson = json.loads(map)

        if not self.workspaceID or not mapJson:
            raise Exception('app service to app insights standard test mapping not found in env vars')

        for k in mapJson.keys():
            keyCleansed = k if k[0] != '/' else ''.join(k[1:])
            self.appServiceAppInsightStandardTestMap[keyCleansed] = mapJson[k]

        self.loaded = True

    def get_standardTestName_by_appsvc_rscId(self, appsvcRscId: str):
        appsvcRscId = appsvcRscId if appsvcRscId[0] != '/' else ''.join(appsvcRscId[1:])
        return self.appServiceAppInsightStandardTestMap[appsvcRscId]
        

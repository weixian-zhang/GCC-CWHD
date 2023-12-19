import json
import os
from logging import Logger

class AppConfig:
    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        self.workspaceID = ''
        self.appServiceAppInsightStandardTestMap = {}
        self.loaded = False

    def load_from_envar(self):
        if self.loaded:
            return
        
        self.workspaceID = os.environ.get('WorkspaceID')
        map = os.environ.get('AppServiceAppInsightStandardTestMap')
        mapJson = json.loads(map)

        for k in mapJson.keys():
            keyCleansed = k if k[0] != '/' else ''.join(k[1:])
            self.appServiceAppInsightStandardTestMap[keyCleansed] = mapJson[k]

        self.loaded = True

    def get_standardTestName_by_appsvc_rscId(self, appsvcRscId: str):
        appsvcRscId = appsvcRscId if appsvcRscId[0] != '/' else ''.join(appsvcRscId[1:])
        return self.appServiceAppInsightStandardTestMap[appsvcRscId]
        

import json
import os
from logging import Logger

class AppConfig:
    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        self.workspaceID = ''
        self.appServiceAppInsightStandardTestMap = {}

    def load_from_envar(self):
        try:
            
            self.workspaceID = os.environ.get('WorkspaceID')
            map = os.environ.get('AppServiceAppInsightStandardTestMap')
            self.appServiceAppInsightStandardTestMap = json.loads(map)
            
        except Exception as e:
            self.logger.debug(e)
        

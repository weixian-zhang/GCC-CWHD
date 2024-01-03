class KQL:

    @staticmethod
    def app_availability_result_query(self, standardTestName):
        return f"""AppAvailabilityResults 
        | where Name == '{standardTestName}' 
        | where TimeGenerated >= ago(2h) 
        | extend availabilityState = iif(Success == true, 'Available', 'Unavailable') 
        | order by TimeGenerated desc 
        | take 1 
        | project ['reportedTime']=TimeGenerated, ['location']=Location, ['Name']=Name, availabilityState"""
    
    @staticmethod
    def cpu_usage_percentage_query(self, resourceId):
        # cpu suage percentage
        return f"""InsightsMetrics
        | where Namespace == "Processor" and Name == "UtilizationPercentage"
        | where TimeGenerated >= ago(1h)
        | where _ResourceId == "{resourceId}"
        | extend CPUPercent = round(Val,0)
        | order by TimeGenerated desc
        | take 1
        | project TimeGenerated, CPUPercent"""

    @staticmethod
    def memory_usage_percentage_query(self, resourceId):
        # memory usage percentage
        return f"""InsightsMetrics
        | where Namespace == "Memory" and Name == "AvailableMB"
        | where TimeGenerated >= ago(1h)
        | where _ResourceId == "{resourceId}"
        | extend DomainName = Computer
        | extend AvailableGB = round(Val/1000,1)
        | extend TotalMemoryGB = round(todecimal(tostring(parse_json(Tags)["vm.azm.ms/memorySizeMB"])) / 1000,1)
        | extend AvailableGB = round(Val/1000,1)
        | extend UsedGB = round((TotalMemoryGB - AvailableGB),1)
        | extend UsedMemoryPercentage = round(((UsedGB / TotalMemoryGB) * 100), 1)
        | order by TimeGenerated desc 
        | take 1
        | project TimeGenerated, UsedMemoryPercentage"""

    @staticmethod
    def disk_usage_percentage_query(self, resourceId):
        
        return f"""InsightsMetrics
        | where Origin == "vm.azm.ms" and Namespace == "LogicalDisk" and Name == "FreeSpacePercentage"
        | where TimeGenerated >= ago(1h)
        | where _ResourceId == "{resourceId}"
        | extend Disk=tostring(todynamic(Tags)["vm.azm.ms/mountId"])
        | extend FreeSpacePercentage = round(Val, 0)
        | extend UsedSpacePercentage = round((100 - FreeSpacePercentage), 0)
        | order by TimeGenerated desc
        | summarize UsedSpacePercentage=round(avg(UsedSpacePercentage),0), round(FreeSpacePercentage=avg(FreeSpacePercentage),0) by Disk
        // join same table to get FreeSpace in GB
        | join kind=inner
            (
                InsightsMetrics
                | where Namespace == "LogicalDisk" and Name == "FreeSpaceMB"
                | where TimeGenerated >= ago(1h)
                | where _ResourceId == "{resourceId}"
                | extend FreeSpaceGB = round(Val /1000,0)
                | extend Disk=tostring(todynamic(Tags)["vm.azm.ms/mountId"])
                | order by TimeGenerated desc
                | summarize FreeSpaceGB=max(FreeSpaceGB) by Disk
            )
            on Disk
        | extend TotalDiskSizeGB = ceiling(FreeSpaceGB / (FreeSpacePercentage / 100))
        | extend UsedSpaceGB = round(TotalDiskSizeGB - FreeSpaceGB, 0)
        | summarize 
        FreeSpacePercentage=max(FreeSpacePercentage),
        FreeSpaceGB=max(FreeSpaceGB), 
        UsedSpacePercentage=max(UsedSpacePercentage),
        UsedSpaceGB=max(UsedSpaceGB),
        TotalDiskSizeGB = max(TotalDiskSizeGB) by Disk"""
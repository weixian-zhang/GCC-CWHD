class KQL:

    @staticmethod
    def app_availability_result_query(standardTestName):
        return f"""AppAvailabilityResults 
        | where Name == '{standardTestName}' 
        | where TimeGenerated >= ago(2h) 
        | extend availabilityState = iif(Success == true, 1, 0) 
        | order by TimeGenerated desc 
        | take 1 
        | project ['reportedTime']=TimeGenerated,  ['availabilityState']=availabilityState"""
    
    def web_app_intranet_connection_monitor_http_test_query(test_group_name):
        return f"""
        NWConnectionMonitorTestResult 
        | where TestGroupName == "{test_group_name}"
        | order by TimeGenerated desc
        | project TimeGenerated, TestResult
        | take 1
        """
    
    @staticmethod
    def cpu_usage_percentage_query(resourceId):
        # cpu suage percentage
        return f"""InsightsMetrics
            | where Namespace == "Processor" and Name == "UtilizationPercentage"
            | where TimeGenerated >= ago(2h)
            | where _ResourceId == tolower("{resourceId}")
            | extend CPUPercent = round(Val,1)
            | order by TimeGenerated desc
            | take 1
            | project TimeGenerated, CPUPercent"""

    @staticmethod
    def memory_usage_percentage_query(resourceId):
        # memory usage percentage
        return f"""InsightsMetrics
        | where Namespace == "Memory" and Name == "AvailableMB"
        | where TimeGenerated >= ago(2h)
        | where _ResourceId == tolower("{resourceId}")
        | extend AvailableGB = round(Val/1000,1)
        | extend TotalMemoryGB = round(todecimal(tostring(parse_json(Tags)["vm.azm.ms/memorySizeMB"])) / 1000,1)
        | extend AvailableGB = round(Val/1000,1)
        | extend UsedGB = round((TotalMemoryGB - AvailableGB),1)
        | extend UsedMemoryPercentage = round(((UsedGB / TotalMemoryGB) * 100), 0)
        | order by TimeGenerated desc 
        | take 1
        | project TimeGenerated, UsedMemoryPercentage"""

    @staticmethod
    def disk_usage_percentage_query(resourceId):
        
        return f"""InsightsMetrics
        | where Origin == "vm.azm.ms" and Namespace == "LogicalDisk" and Name == "FreeSpacePercentage"
        | where TimeGenerated >= ago(2h)
        | where _ResourceId == tolower("{resourceId}")
        | extend Disk=tostring(todynamic(Tags)["vm.azm.ms/mountId"])
        | extend FreeSpacePercentage = Val
        | extend UsedSpacePercentage = (100 - FreeSpacePercentage)
        | order by TimeGenerated desc
        | summarize UsedSpacePercentage=avg(UsedSpacePercentage), FreeSpacePercentage=avg(FreeSpacePercentage) by Disk
        // join same table to get FreeSpace in GB
        | join kind=inner
            (
                InsightsMetrics
                | where Namespace == "LogicalDisk" and Name == "FreeSpaceMB"
                | where TimeGenerated >= ago(2h)
                | where _ResourceId == tolower("{resourceId}")
                | extend FreeSpaceGB = Val /1000
                | extend Disk=tostring(todynamic(Tags)["vm.azm.ms/mountId"])
                | order by TimeGenerated desc
                | summarize FreeSpaceGB=max(FreeSpaceGB) by Disk
            )
            on Disk
        | extend TotalDiskSizeGB = FreeSpaceGB / (FreeSpacePercentage / 100)
        | extend UsedSpaceGB = TotalDiskSizeGB - FreeSpaceGB
        | summarize 
        FreeSpacePercentage=round(max(FreeSpacePercentage), 2),
        FreeSpaceGB=round(max(FreeSpaceGB), 2), 
        UsedSpacePercentage=round(max(UsedSpacePercentage),0),
        UsedSpaceGB=round(max(UsedSpaceGB), 2),
        TotalDiskSizeGB = round(max(TotalDiskSizeGB), 2) by Disk"""

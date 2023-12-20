# GCC-CWHD  

<p>CWHD currently monitors 2 Apps OneLogin and Documentum. Level 0 dashboard is a simple dashboard showing the "overall" Azure resource availability status of each App.</p>
<p>The "overall" available status depends on the dependent Azure resources that each App is using.  </p>
For example OneLogin is backed by 3 Azure resources: App Service, Key Vault and APIM. The overall availability status will only be available when all 3 resourcecs' availability status is Available.  

### Architecture  

Resource Health Retriever Function can retrieve health status from different sources depending on different resource types.  
Currently, function supports the following:
  * "General" resource types (all non App Service types): get their health status from [Azure Resource Health](https://learn.microsoft.com/en-us/azure/service-health/resource-health-overview) via [Resource Health Rest API](https://learn.microsoft.com/en-us/rest/api/resourcehealth/availability-statuses?view=rest-resourcehealth-2022-10-01).
    
  * App Service: in the case of App Service, function performs [log query](https://devblogs.microsoft.com/azure-sdk/announcing-the-new-azure-monitor-query-client-libraries/) from Log Analytics AppAvailabilityResults table to get the latest Standard Test result. Reason for not getting health status from Resource Health API is that when an App Service is stopped, Resource Health still shows "Available" as this is behaviour is by design. Requirement is to show "Unavailable" when an App Service is stopped.
    
  * VM (future enhancement): VM health status signal from [Resource Health](https://learn.microsoft.com/en-us/azure/service-health/resource-health-overview) can be further influenced by addition metrics like CPU and Memory when these metrics exceeds configured threshold.

<img width="486" alt="image" src="https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/11aee8f4-2c0b-42cc-8e75-547c8576a642">



### Level 0 Dashboard  

![image](https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/13bd3524-f694-4c39-b1df-4b43244a0cbd)


### Level 1 - OneLogin  

![image](https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/8c259cc2-72bd-4583-bf99-c7d72bee039c)


### Level 1 - Documentum  

![image](https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/7f686ed0-902c-4213-a021-0174a6a08e65)


### Level1 - Azure API Management Dashboard, 3rd-Party

Dashboard courtesy from [Vikram Bala](https://grafana.com/grafana/dashboards/16604-azure-api-management/)

![image](https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/35b24813-7335-42ea-b43d-9ff68a718be4)



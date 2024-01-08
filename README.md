# GCC-CWHD  

CWHD currently provides Grafana dashboards to visualize Azure resource health statuses and metrics for 2 web apps OneLogin and Documentum.  
The dashboards are organized in levels depicting the "depth" of monitoring. 
  * Level 0 dashboard shows the "overall" Azure resource availability status of each App.  
    The overall available status depends on the dependent Azure resources that each web app is using.  
    For example OneLogin is backed by 3 Azure resources: App Service, Key Vault and APIM. The overall availability status will only be available when all 3 
    resourcecs' availability status is Available.
    
  * Level 1 dashboard are web app specific, it displays the health and metrics of specific Azure resources used by web app

<br />

### Architecture  

<img width="600" height="700" alt="image" src="https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/32769d2a-10de-4c92-bffa-d34d5eb77386">


CWHD uses a variety of Azure components including a custom Function named Resource Health Retriever, acting as health status aggregator that retrieves and aggregates health statuses from different data sources depending on different resource types.  

In the health status aspect of CWHD, Resource Health Retriever function supports the following:
  * "General" resource types (all non App Service types): get their health status from [Azure Resource Health](https://learn.microsoft.com/en-us/azure/service-health/resource-health-overview) via [Resource Health Rest API](https://learn.microsoft.com/en-us/rest/api/resourcehealth/availability-statuses?view=rest-resourcehealth-2022-10-01).
    
  * App Service: function performs [log query](https://devblogs.microsoft.com/azure-sdk/announcing-the-new-azure-monitor-query-client-libraries/) from Log Analytics AppAvailabilityResults table to get the latest Standard Test result. Reason for not getting health status from Resource Health API is that when an App Service is stopped, Resource Health still shows "Available", this behaviour is by design. Requirement is to show "Unavailable" when an App Service is stopped.
    
  * VM: A VM's health status is determine by 2 factors
    * [Resource Health](https://learn.microsoft.com/en-us/azure/service-health/resource-health-overview) availability status determines if VM is available or not depicting the Green or Red status.
    * 3 metrics CPU, Memory and Disk usage percentage if crosses a configurable threshold, Grafana panel of VM resource will show Amber status. Amber status is shown only if Resource Health availability status is Green/Available. If Unavailable/Red, Red will be shown even if any metrics reaches threshold.



### Level 0 Dashboard  

{updating to latest screenshot}

If there is any one of the Azure resource used by OneLogin or Documentum that has an "Unavailable" status, the overall health status at Level 0 will be Unavailable.


### Level 1 - OneLogin  

{updating to latest screenshot}


### Level 1 - Documentum  

{updating to latest screenshot}


### Level 1 - Azure API Management Dashboard, 3rd-Party

Dashboard courtesy from [Vikram Bala](https://grafana.com/grafana/dashboards/16604-azure-api-management/)

![image](https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/35b24813-7335-42ea-b43d-9ff68a718be4)



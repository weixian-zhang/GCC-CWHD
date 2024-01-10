# GCC-CWHD  

CWHD currently provides Grafana dashboards to visualize Azure resource health statuses and metrics for 2 web apps CloudCrafty and PocketGeek.  
The dashboards are organized in levels depicting the "depth" of monitoring. 
  * Level 0 dashboard shows the "overall" Azure resource availability status of each App.  
    The overall available status depends on the dependent Azure resources that each web app is using.  
    For example CloudCrafty is backed by 3 Azure resources: App Service, Key Vault and APIM. The overall availability status will only be available when all 3 
    resourcecs' availability status is Available.
    
  * Level 1 dashboard are web app specific, it displays the health and metrics of specific Azure resources used by web app

<br />

### Architecture  

<img width="600" height="700" alt="image" src="https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/47b01407-8a38-4b44-a63a-befd38198928">


CWHD uses a variety of Azure resources including a core Azure Function named Resource Health Retriever, acting as health status aggregator to retrieve and aggregate metrics and health statuses from different data sources depending on the resource types under monitoring.  

In the health status aspect of CWHD, Resource Health Retriever function supports the following:
  * "General" resource types (all non App Service types): get their health status from [Azure Resource Health](https://learn.microsoft.com/en-us/azure/service-health/resource-health-overview) via [Resource Health Rest API](https://learn.microsoft.com/en-us/rest/api/resourcehealth/availability-statuses?view=rest-resourcehealth-2022-10-01).
    
  * App Service: function performs [log query](https://devblogs.microsoft.com/azure-sdk/announcing-the-new-azure-monitor-query-client-libraries/) from Log Analytics AppAvailabilityResults table to get the latest Standard Test result. Reason for not getting health status from Resource Health API is that when an App Service is stopped, Resource Health still shows "Available", this behaviour is by design. Requirement is to show "Unavailable" when an App Service is stopped.
    
  * VM: health status is determine by 2 factors
    * [Resource Health](https://learn.microsoft.com/en-us/azure/service-health/resource-health-overview) availability status determines if VM is available or not depicting the Green or Red status.
    * If resource health status is Available/Green, additional 3 metrics CPU, Memory and Disk usage percentage will be monitored according to a set of configurable thresholds.
      In Grafana, VM Stat visualization  will show Amber status if one or more of the 3 metrics reaches the threshold.



### Level 0 Dashboard  

<img width="876" alt="image" src="https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/8c23c138-cdde-4cf6-b16b-05466122cd4c">


If there is any one of the Azure resource used by OneLogin or Documentum that has an "Unavailable" status, the overall health status at Level 0 will be Unavailable.


### Level 1 - Cloud Crafty  

<img width="877" alt="image" src="https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/986ec27c-f2fc-41a0-9b4d-72bdf23d42ba">


### Level 1 - Pocket Geek  

<img width="879" alt="image" src="https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/c3729a68-295e-41e5-a03a-49e67e2c4ec0">  

<img width="877" alt="image" src="https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/18096f20-abb4-424e-8fde-3e8fcd42f5a0">


### Level 1 - Azure API Management Dashboard, 3rd-Party

Dashboard courtesy from [Vikram Bala](https://grafana.com/grafana/dashboards/16604-azure-api-management/)

![image](https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/35b24813-7335-42ea-b43d-9ff68a718be4)



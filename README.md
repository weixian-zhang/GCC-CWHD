# GCC Azure - Central Workload Health Dashboard (AZCWHD)
 
CWHD is a custom Azure monitoring solution leveraging Grafana to monitor the following aspects:  

  Color code signals in Grafana dashboards showing Green, Amber and Red tiles depending on:
   * overall resource heath from Azure Resource Health signals
   * all App health using App Insights Standard Test (HTTP ping) web app availability signals
    * for VM only - configurable threshold of CPU, Memory and Disk usage to display Amber color when threshold is met.
    (only works for VM)
  * dashboard visualization tiles uses Green, Amber and Red color code to determine the overall availability of an application aggregated by one or more Azure resource's Resource Health

The dashboards are organized in Level 0 and Level 1 depicting the "depth" of monitoring. 
  * Level 0 - shows availability status if all Apps.  
  * Level 1 - drills into Resource Health of each Azure resource used by the app

<br />

* [Tech Stack](#tech-stack)
* [Telemtry Required](#telemtry-required)
* [Deployment & Configuration ](#deployment--configuration)
* [Architecture](#architecture)
* [Level 0 dashboard](#level-0-dashboard)
* [Level 1 dashboard](#level-1---cloud-crafty-dashboard)
* [Level 2 dashboard](#level-2-dashboard)

<br />  

## Tech Stack  
* Python 3.11
* Azure Managed Grafana Standard - Grafana 10.4.11
* [Docker](https://github.com/weixian-zhang/GCC-CWHD/blob/main/src/telemetry_forager/Dockerfile)

## Telemtry Required

   * for App Service health signal - based on any one of the following available result
     * Application Insights Availability Test result
     * Network Watcher Connection Monitor
     * lastly, Resource Health if any of the above isnot available
   * for Virtual Machines health signal - enable [VM Insights](https://learn.microsoft.com/en-us/azure/azure-monitor/vm/vminsights-enable-overview#vm-insights-data-collection-rule)
   * for rest of resource types - defaults to Resource Health
 
## Deployment & Configuration 
1.  App Service for Containers
    * container image - from Dockerhub image [wxzd/cwhd:v1.1.1](https://hub.docker.com/layers/wxzd/cwhd/v1.1.1/images/sha256-d36e9b8868efd0cc223237a1c7ee4df20c5e64a814f034dc9f9b8e8fdcd5147f)
    * App Service Plan - Standard S1, Premium v3 P0V3 or higher
    * Environment Variables
      * <b>APPLICATIONINSIGHTS_CONNECTION_STRING</b>={conn string}
      * <b>HealthStatusThreshold</b>={"metricUsageThreshold": {         "vm": {             "cpuUsagePercentage": 80,             "memoryUsagePercentage": 80,             "diskUsagePercentage": 80         }     } }
      * <b>QueryTimeSpanHour</b>=2
      * <b>WEBSITES_PORT</b>=8000
      * <b>Version</b>=1.1.1
    * enable Managed Identity
      * add Azure role assignment (RBAC) for Managed Identity with [Monitor Reader](https://learn.microsoft.com/en-us/azure/azure-monitor/roles-permissions-security#monitoring-reader) to:
         *  Subscriptions containing resources under monitoring
         *  Log Analytics Workspace (if workspace in different subscription from above)
    *  Enable Application Insights
    * Setup [Easy Auth](https://learn.microsoft.com/en-us/azure/app-service/overview-authentication-authorization) with Microsoft Provider
      * <b>Easy Auth GUI experience will auto create a service principal with name similar to App Service name. Add "Monitoring Reader" role for service principal to App Service</b>

2.  Azure Managed Grafana
     *  Sku = Standard
     *  enable Managed Identity
        *  add Azure role assignment (RBAC) for Grafana Managed Identity with [Monitor Reader](https://learn.microsoft.com/en-us/azure/azure-monitor/roles-permissions-security#monitoring-reader) to:
           *  Subscriptions containing resources under monitoring
           *  Log Analytics Workspaces (if workspaces are in different subscription from above)
     *  [Infinity](https://grafana.com/grafana/plugins/yesoreyeram-infinity-datasource/) plugin
        *  Add Infinity plugin
        *  Configure Infinity data source authn with Entra ID
           * Client Id (App Service Easy Auth service principal)
           * Client secret (App Service Easy Auth service principal)
           * Token Url: https://login.microsoftonline.com/{tenant id}/oauth2/token
           * Endpoint param: Resource : api://{client id} e.g: api://73667734-67cf-49e9-96e1-927ca23d6c18
           * Allowed hosts:	{Domain of App Service} e.g: https:// web-container-cwhd-e3cxcfdyg6bdfza7.southeastasia-01.azurewebsites.net
        *  Test if Infinity data source is able to authenticate with CWHD web app 
 
<br />


### Architecture  

<img width="550" height="700" alt="image" src="https://github.com/user-attachments/assets/06104765-6dff-482a-b48c-fe6b321939f0">  

<br />
<br />

Telemetry Forager is the backend service that curates telemetry from different data sources including:

 * Azure Monitor REST API
   * App Service health status determine by any one of the following result:
     * Kusto query - Application Insights Availability Test result (AppAvailabilityResults table)
     * Kusto query - Network Watcher Connection Monitor (NWConnectionMonitorTestResult table)
     * Resource Health API as last option to determine health status if above options are not available
   * VM: health status is determine by 2 factors
     * [Resource Health](https://learn.microsoft.com/en-us/azure/service-health/resource-health-overview) availability status determines if VM is available or not depicting the Green or Red status.
     * If resource health status is Available/Green, Log Analytics Workspace ID is provided,
       additional 3 metrics of CPU, Memory and Disk usage percentage will be monitored according to a set of configurable thresholds.
       In Grafana, VM Stat visualization  will show Amber status if one or more of the 3 metrics reaches the threshold.
 * [Azure Resource Health API](https://learn.microsoft.com/en-us/rest/api/resourcehealth/availability-statuses?view=rest-resourcehealth-2022-10-01) - get resource health for all resource types except App Service, which gets health status from App Insight Standard Test

### Telemetry Forager API Spec  

<table>
  <tr>
    <th>Path</th>
    <th>Method</th>
    <th>Param</th>
  </tr>
  <tr>
    <td>/RHRetriever</td>
    <td>POST</td>
    <td>
     { <br />
      "resources": [ <br />
          { [ <br />
              "resourceId":"{resource id}", [ <br />
              "standardTestName": "{ App Insights standard test name }", [ <br />
  			         "workspaceId": "{Log Analytics Workspace Id}" [ <br />
          &nbsp&nbsp}  <br />
         &nbsp] <br />
      } <br />
    </td>
  </tr>
</table>

    
<br />  

## Samples  

### Level 0 Dashboard  

<img width="876" alt="image" src="https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/8c23c138-cdde-4cf6-b16b-05466122cd4c">



 The overall available status (green) depends on the dependent Azure resources that each app here is using.
 If there is any one of the Azure resource used by Cloud Crafty or Pocket Geeks apps that has Resource Health status as "Unavailable", the overall health status at Level 0 will be Unavailable.
 For example Cloud Crafty uses 3 Azure resources: App Service, Key Vault and APIM. The overall availability status will only be Green when all 3 
 resourcecs' Resource Health + App Insight Standard Test availability status is available.

### Level 1 - Cloud Crafty Dashboard

<img width="876" alt="image" src="https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/2d395168-3729-4982-8915-9eb11e44ca78">



### Level 1 - Pocket Geek Dashboard 

<img width="879" alt="image" src="https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/c3729a68-295e-41e5-a03a-49e67e2c4ec0">  

<img width="877" alt="image" src="https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/18096f20-abb4-424e-8fde-3e8fcd42f5a0">


### Level 2 Dashboard

Proposed Distributed Tracing with OpenTelemetry Collector to collect OpenTelemetry traces from apps, collector sends traces to Jaeger backed by Azure Managed Cassandra.
Grafana gets traces from Jaeger as datasource to display traces within Grafana centrally, in addition to viewing traces in Jaeger UI.



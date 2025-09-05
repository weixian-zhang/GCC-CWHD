<h2>
 <p>Cloud Workload Health Dashboard (CWHD) | Project Heimdall</p>
</h2>
</h2>

 <mark>Warning: Important information for customers using Central Workload Health Dashboard</b> <br />
 This solution, offered by the Open-Source community, does not receive contributions nor support by Microsoft.</mark>

<br />

### Trusted by agencies on [GCC](https://www.tech.gov.sg/products-and-services/for-government-agencies/software-development/government-on-commercial-cloud/), CWHD uses Grafana for Azure Monitoring

<br />

* [Tailor-Made](#tailor-made-dashboards)
    - [Tier 1 Dashboard](#tier-1-dashboard)
    - [Tier 0 Dashboard](#tier-0-dashboard)
    - [The Colored Tile Concept](#the-colored-tile-concept)
      
* [Ready-Made](#ready-made-dashboards)
    - [Network Map (Preview)](#network-map-preview)
    - [WARA Dashboard (Pending Update)](#wara-dashboard-pending-update-due-to-wara-repo-changed)
    - [Activity Audit Dashboard](#activity-audit-dashboard)
    - [Firewall Dashboard](#firewall-dashboard)

- [Tech Stack](#tech-stack)
- [Logs Required](#logs-required)
- [Deployment \& Configuration](#deployment--configuration)
- [CWHD Backend REST API Spec](#cwhd-backend-rest-api-spec)
- [Architecture](#architecture)

<br />  

## Tailor-Made Dashboards  

As each monitoring scenario is unique, Tailor-Made dashboards are built from scratch from custom requirements but have a choice to follow the hierarchical [Colored Tile](#the-colored-tile-concept) concept below.

### Tier 1 Dashboard

You aim to to cohesively group up all dependent Azure resources into a Tier 1 dashboard. How do you want to group resources is entirely up to you, below is a general guideline:
<ul>
 <li>
  <b>Group by system</b>
  <div>
   For e.g: You have a system that leverages App Services, VMs, Redis Cache, Azure SQL, Storage, Azure OpenAI service and Azure Function.
   If any one or more of these services fails your system will be affected. The Tier 1 dashboard should monitor all these Azure resources that together supports the functioning of your system.
  </div>
  <br />
  <div>
   <p></p>For example if you have 2 systems Cloud Crafty and Pocket Geek, you will have two Tier 1 dashboards.</p>
   
   <div>
   <b>Tier 1 / Cloud Crafty</b>
   <img alt="image" src="https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/2d395168-3729-4982-8915-9eb11e44ca78">
   </div>
   </div>
  
   <div>
   <b>Tier 1 / Pocket Geek</b>
   <img alt="image" src="https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/c3729a68-295e-41e5-a03a-49e67e2c4ec0">
   <img alt="image" src="https://github.com/user-attachments/assets/44d31b51-106e-49a7-a3a6-24e73fa01c69">
   </div>
 </li>
 
 <li>
  <b>Group by Subscription/Resource Group</b>
  <div>
   The context could be cloud admin monitoring shared resources in landing zones and shared resources are already grouped by Subscription or Resource Group.  
   In this case, 1 subscription = Tier 1 dashbaord
  </div>
 </li>

  <li>
  <b>Group scattered resources</b>
  <div>
   You could also group Azure resources from different subscriptions and resource groups into a Tier 1 dashboard.
  </div>
 </li>
</ul>

<br />  

### Tier 0 Dashboard

This dashboard is a summary view of all Tier 1 dashboards.  
Similar to Tier 1 dashboards, CWHD cannot offer pre-built dashboards as Tier 0 and 1 are fully customized and adapted to your specific grouping of resources.
<div>For this reason, Tier 0 and 1 dashboards is the core delivery work I will do for my customers, in addition to other custom request for e.g: IIS App Pool start/stop</div>

<br />
<img alt="image" src="https://github.com/user-attachments/assets/1a66114c-87d5-4239-8ef5-5cb13bc7390d">
<img alt="image" src="https://github.com/user-attachments/assets/1cc9baa2-27a8-464a-ba0f-8300f23bf5f1">

<br />  
<br />  

## The Colored Tile Concept

Colored tiles exist in Tier 0 and 1 dashboards only and each Azure resource is represented by a color-coded tile.  
Each color-coded tile displays one of the 3 colors at any one time: Green, Amber and Red which represents the different health status.   
<img src ="https://github.com/user-attachments/assets/2ec6e7b4-0f75-49a3-9894-82f3701eeb46" height="150px" width="500px" />

* Green
  * health status from Azure Resource Health API is healthy
  * for App Service specifically, health status are determined by either one of the following data source
    * Application Insights Availability Test
    * Network Watcher Connection Monitor
    * Azure Resource Health API
  * when all resources in Tier 1 color-coded tiles are Green, Tier 0 summarizes system status as Green
  <img src="https://github.com/user-attachments/assets/7c9b6c15-b36c-4a07-9e05-75aef7ea67c0" height="250px" width="600px" />
  
* Amber
  * affects only Virtual Machine resources. if VM's CPU, Memory and/or Disk usage percentage hits threshold. amber color will be shown. See [Deployment & Configuration](#deployment--configuration)
  * when any one of VM in Tier 1 color-coded tiles is Amber, Tier 0 dashboard summarizes system status as Amber
    <img src="https://github.com/user-attachments/assets/f2a29c10-899a-48d8-92d2-d8ae8043bf94" height="250px" width="600px" />

* Red
  * when Resource Health API returns unhealthy result
  * for App Service specifically, if either of the following returns unhealthy status
    * Application Insights Availability Test
    * Network Watcher Connection Monitor
    * Azure Resource Health API
  * when any one resource in Tier 1 color-coded tiles is Red, Tier 0 dashboard summarizes system status as Red. Red is "larger" than Amber.
  
    <img src="https://github.com/user-attachments/assets/98540059-8286-4c4b-8795-aeb23c0dc991" height="300px" width="650px" />

## Ready-Made Dashboards

* [Network Map (Preview)](#network-map-preview)
* [WARA Dashboard (Pending Update)](#wara-dashboard-pending-update-due-to-wara-repo-changed)
* [Activity Audit Dashboard](#activity-audit-dashboard)
* [Firewall Dashboard](#firewall-dashboard)

<br />
<br />

### Network Map (Preview)  

This latest dashboard helps you visualize [VNet Flow Logs](https://learn.microsoft.com/en-us/azure/network-watcher/vnet-flow-logs-overview?tabs=Americas) processed by [Azure Traffic Analytics](https://learn.microsoft.com/en-us/azure/network-watcher/traffic-analytics?tabs=Americas) as directed graph.
* Setup
  * Currently previewing on Windows container image [wxzd/cwhd:networkmap-v0.2.0 ](https://hub.docker.com/r/wxzd/cwhd/tags)
  * deploy [Python-backend](#architecture) on App Service Windows Container
  * Need to enable VNet Flow Logs and Traffic Analytics
  * required Grafana pluging:
    * Infinity
    * Business Charts
    * Business Table
    * Business Variable
* Network Map Grafana dashboard can be imported [here](https://github.com/weixian-zhang/GCC-CWHD/blob/feat/networkmap/src/dashboards/tier-2/networkmap.json)
* try to keep data small as large amount of nodes in thousands can cause graph to render slowly
* to zoom and move graph, move cursor closer to graph.

![image](https://github.com/weixian-zhang/GCC-CWHD/blob/main/doc/networkmap.gif)

![image](https://github.com/user-attachments/assets/7a15bb76-bc69-4529-b78f-c963e94173f4)

<br />

### WARA Dashboard ([pending update due to WARA repo changed](https://azure.github.io/Azure-Proactive-Resiliency-Library-v2/tools/collector/#quick-workflow-example))

CWHD runs [Azure WARA assessment](https://azure.github.io/Azure-Proactive-Resiliency-Library-v2/welcome/) on startup and subsequently every 6 hourly schedule to bring you the past and latest reliability states of your Azure environment.
<p>
 Under the hood, on every WARA run, CWHD downloads the latest copy of <a href="https://azure.github.io/Azure-Proactive-Resiliency-Library-v2/tools/collector">collector.ps1</a> and <a href="https://azure.github.io/Azure-Proactive-Resiliency-Library-v2/tools/analyzer">analyzer.ps1</a> and executes these 2 scripts to produce assessment result.  
 Result is then formatted and publish via CWHD-Backend REST APIs to be consumed by Grafana.
</p>

 * dashboard requires Grafana 11 due to [Business Table](https://grafana.com/grafana/plugins/volkovlabs-table-panel/)
 * CWHD backend runs on Windows Container

![image](https://github.com/user-attachments/assets/fc8254b2-faeb-4509-9ed6-e4bfb43f7196)

![image](https://github.com/user-attachments/assets/2c50ea6f-27bf-427a-999d-5540baf26423)

Able to select by past and latest reports and filter by subscription  

![image](https://github.com/user-attachments/assets/3ac15834-be09-4aa4-af3d-69763a8a5085)  

<br />

#### Activity Audit Dashboard
  <p>Shows you who made changes to Firewall rules, NSG rules, Key Vaults opearations and oerations of all other Azure services</p>  
  
  ![image](https://github.com/user-attachments/assets/ef0ca381-bcf6-4d1d-84c1-7fd61d301283)

<br />


### Firewall Dashboard
  ![image](https://github.com/user-attachments/assets/413d5f54-760f-4ac6-8423-7190860835d3)
  ![image](https://github.com/user-attachments/assets/7aa1993c-c590-494a-9bc0-e2dd500bde83)

<br />

## Tech Stack  
* Python 3.11
* Azure Managed Grafana Standard - Grafana 10.4.11
* [Docker image](https://hub.docker.com/r/wxzd/cwhd/tags)

## Logs Required
<table>
  <tr>
    <th>Grafana Dashboards</th>
    <th>Logs required in Workspace</th>
  </tr>
  <tr>
    <td>
     <ul>
       <li>Tier 0 resource specific dashboard</li>
       <li>Tier 1 resource specific dashboard</li>
     </ul>
    </td>
    <td>
      <ul>
          <li>
            App Service health signal - either one of the following logs
            <ul>
              <li>Application Insights Availability Test result</li>
              <li>Network Watcher Connection Monitor</li>
              <li>Resource Health API if above are not available</li>
            </ul>
          </li>
          <li>
            <span></span>Virtual Machine CPU, Memory and Disk usage percentage  requires Performance Counters
            collected by Data Collection Rule / Data Sources / Performance Counters - Basic -> / Destination / Log Analytics Workspace</li></ul></td>
            </span>
          </li>
        </ul>
     </td>
  </tr>

 <tr>
    <td>
     Tier 2 / Activity Audit dashboard
    </td>
    <td>
       send Activity Log to Workspace
    </td>
 </tr>
 
 <tr>
    <td>
     Tier 2 / Firewall dashboard
    </td>
    <td>
        enable Firewall diagnostics settings
        <ul>
          <li> Azure Firewall Network Rule</li>
          <li> Azure Firewall Application Rule</li>
          <li> Azure Firewall Nat Rule</li>
          <li> Azure Firewall Threat Intelligence</li>
          <li> Azure Firewall IDPS Signature</li>
          <li> Azure Firewall DNS query</li>
        </ul>
    </td>
  </tr>

  <tr>
    <td>
     Tier 2 / API Management dashboard
    </td>
    <td>
      enable APIM diagnostics settings
      <ul>
        <li>
          <ul>
            <li>Logs related to APIManagement Gateway</li>
          </ul>
        </li>
        <li>
          enable Application Insights linked to Workspace
        </li>
      </ul>
    </td>
  </tr>

  <tr>
    <td>
     Tier 2 / Application Gateway dashboard
    </td>
    <td>
     <ul>
       <li>
        enable App Gateway diagnostics settings
        <ul>
          <liApplication Gateway Access Log</li>
          <li>Application Gateway Performance Log</li>
          <li>Application Gateway Firewall Log</li>
        </ul>
       </li>
       <li>enable Application Insights linked to Workspace</li>
     </ul>
    </td>
  </tr>

  <tr>
    <td>
     Tier 2 / Key Vault dashboar
    </td>
    <td>
      enable Key Vault diagnostics settings
      <ul>
        <li>Audit Logs  </li>
      </ul>
    </td>
  </tr>
  
</table>  

 
## Deployment & Configuration 
1.  App Service for Containers
    * Publish = Container
    * Operating System = Linux
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
    * Setup [Easy Auth](https://learn.microsoft.com/en-us/azure/app-service/overview-authentication-authorization#how-it-works) with Microsoft Provider
      * Option 1: [Create and use new App registration](https://learn.microsoft.com/en-us/azure/app-service/configure-authentication-provider-aad?tabs=workforce-configuration#express)
      * Option 2: [Use an existing registration created separately](https://learn.microsoft.com/en-us/azure/app-service/configure-authentication-provider-aad?tabs=workforce-configuration#-option-2-use-an-existing-registration-created-separately).
        Entra ID App configuration example below.  
        <img src = "https://github.com/user-attachments/assets/e8388734-d499-4977-a768-b8fde7ea185e" height="350px" width="700px" />

        <img src = "https://github.com/user-attachments/assets/b69880e0-41b1-45e6-bdce-36194970d65a" height="350px" width="700px" />

        <img src = "https://github.com/user-attachments/assets/f063c6c2-8f15-42cf-b42e-6294933b26f5" height="350px" width="700px" />

        <img src = "https://github.com/user-attachments/assets/c0d053c4-cd6b-4f8e-88a7-b0a7c90026dc" height="400px" width="700px" />

    * Networking / Access Restrictions / Site access and rules (After Managed Grafana is deployed and configured)
      * Public network access = "Enabled from selected virtual networks and IP addresses"
      * Unmatched rule action = Deny
      * add 2 Grafana Static IP addresses found under "Deterministic outbound IP"

1.  Azure Managed Grafana
     *  Sku = Standard
     *  enable Managed Identity
        *  add Azure role assignment (RBAC) for Grafana Managed Identity with [Monitor Reader](https://learn.microsoft.com/en-us/azure/azure-monitor/roles-permissions-security#monitoring-reader) to:
           *  Subscriptions containing resources under monitoring
           *  Log Analytics Workspaces (if workspaces are in different subscription from above)
     *  [Infinity](https://grafana.com/grafana/plugins/yesoreyeram-infinity-datasource/) plugin
        *  Plugin Management, add plugins
           * Infinity
           * Business Variable
           Select and hit "Save"
        *  Configure Infinity data source authn with Entra ID
           * Auth type = OAuth2
           * Grant type = Client Credentials  
           * Client Id (App Service Easy Auth service principal)
           * Client secret (App Service Easy Auth service principal)
           * Token Url: https://login.microsoftonline.com/{tenant id}/oauth2/token
           * Endpoint param: Resource : api://{client id} e.g: api://73667734-67cf-49e9-96e1-927ca23d6c18
           * Allowed hosts:	{Domain of App Service} e.g: https://web-container-cwhd-e3cxcfdyg6bdfza7.southeastasia-01.azurewebsites.net
        *  Test if Infinity data source is able to authenticate with CWHD web app
        *  Configuration / Deterministic outbound IP - Enable
 
<br />

### CWHD Backend REST API Spec  

<table>
  <tr>
    <th>Path</th>
    <th>Method</th>
    <th>Input Param</th>
    <th>Description</th>
  </tr>
  <tr>
    <td>/</td>
    <td>GET</td>
    <td>
    </td>
    <td>
     Root path returns "alive"
    </td>
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
              "network_watcher_conn_mon_test_group_name": "{network watcher connection monitor test group name}"
          &nbsp&nbsp}  <br />
         &nbsp] <br />
      } <br />
    </td>
    <td>
     standardTestName and network_watcher_conn_mon_test_group_name are optional params for getting App Service health and will fall back to Resource Health API if not supplied
    </td>
  </tr>
</table>

<br />

### Architecture  

![image](https://github.com/user-attachments/assets/b6b88bbb-135d-4ff7-b371-e613cd4077bd)

<br />
<br />

CWHD Python-Backend is a web app that curates telemetry from different data sources including:

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



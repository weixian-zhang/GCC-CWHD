# GCC-CWHD  

<p>CWHD currently monitors 2 Apps OneLogin and Documentum. Level 0 dashboard is a simple dashboard showing the "overall" Azure resource availability status of each App.</p>
<p>The "overall" available status depends on the dependent Azure resources that each App is using.  </p>
For example OneLogin is backed by 3 Azure resources: App Service, Key Vault and APIM. The overall availability status will only be available when all 3 resourcecs' availability status is Available.  

### Architecture  

Resource Health Retriever Function calls [Resource Health API](https://learn.microsoft.com/en-us/rest/api/resourcehealth/availability-statuses/get-by-resource?view=rest-resourcehealth-2022-10-01&tabs=HTTP) to retrieve resource health by resource ID as parameter

<img width="373" alt="image" src="https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/9b18b88e-9c7b-4b02-954b-f614fce6b340">


### Level 0 Dashboard  

![image](https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/c194b280-a742-440c-8017-7837c322a30e)


### Level 1 - OneLogin  

![image](https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/d8fb3ed6-659b-4c81-ace9-970fa4f99695)



### Level 1 - Documentum  

![image](https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/5ea45b3c-b39b-41f6-94a9-2c446494f6e7)


### Level1 - Azure API Management Dashboard, 3rd-Party

Dashboard courtesy from [Vikram Bala](https://grafana.com/grafana/dashboards/16604-azure-api-management/)

![image](https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/35b24813-7335-42ea-b43d-9ff68a718be4)



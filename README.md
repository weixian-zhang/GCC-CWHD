# GCC-CWHD  

<p>CWHD currently monitors 2 Apps OneLogin and Documentum. Level 0 dashboard is a simple dashboard showing the "overall" Azure resource availability status of each App.</p>
<p>The "overall" available status depends on the dependent Azure resources that each App is using.  </p>
For example OneLogin is backed by 3 Azure resources: App Service, Key Vault and APIM. The overall availability status will only be available when all 3 resourcecs' availability status is Available.  

### Architecture  

Resource Health Retriever Function calls [Resource Health API](https://learn.microsoft.com/en-us/rest/api/resourcehealth/availability-statuses/get-by-resource?view=rest-resourcehealth-2022-10-01&tabs=HTTP) to retrieve resource health by resource ID as parameter

<img width="373" alt="image" src="https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/9b18b88e-9c7b-4b02-954b-f614fce6b340">


### Level 0 Dashboard  

![image](https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/79eacfc8-dce5-49ff-8eaa-27425fb9c909)  

### Level 1 - OneLogin  

![image](https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/b05f44f9-41a0-42ec-a10e-c0623a8120e4)


### Level 1 - Documentum  

![image](https://github.com/weixian-zhang/GCC-CWHD/assets/43234101/8824791f-0f29-406a-952a-7ec996b0af1b)


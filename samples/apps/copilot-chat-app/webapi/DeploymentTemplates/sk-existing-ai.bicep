/*
Copyright (c) Microsoft. All rights reserved.
Licensed under the MIT license. See LICENSE file in the project root for full license information.

Bicep template for deploying Semantic Kernel to Azure as a web app service without creating a new Azure OpenAI instance.

TODO: pass in completion and embedding models as parameters.

Resources to add:
- Qdrant
- CosmosDB
- AzureSpeech
- vNet + Network security group
- Key Vault
*/

@description('Name for the deployment')
param name string = 'sk'

@description('SKU for the Azure App Service plan')
param appServiceSku string = 'B1'

@description('Location of package to deploy as the web service')
#disable-next-line no-hardcoded-env-urls // This is an arbitrary package URI
param packageUri string = 'https://skaasdeploy.blob.core.windows.net/api/skaas.zip'

@description('Azure OpenAI endpoint to use (ignored when using non-Azure instance)')
param endpoint string = ''

@secure()
@description('Azure OpenAI or OpenAI API key')
param apiKey string = ''


@description('Region for the resources')
#disable-next-line no-loc-expr-outside-params // We force the location to be the same as the resource group's for a simpler,
var location = resourceGroup().location       // more intelligible deployment experience at the cost of some flexibility

@description('Name for the deployment - Made unique')
var uniqueName = '${name}-${uniqueString(resourceGroup().id)}'


resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: '${uniqueName}-plan'
  location: location
  sku: {
    name: appServiceSku
  }
}

resource appServiceWeb 'Microsoft.Web/sites@2022-03-01' = {
  name: '${uniqueName}-web'
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      alwaysOn: true
      detailedErrorLoggingEnabled: true
      minTlsVersion: '1.2'
      netFrameworkVersion: 'v6.0'
      use32BitWorkerProcess: false
      appSettings: [
        {
          name: 'Service:SemanticSkillsDirectory'
          value: ''
        }
        {
          name: 'Service:KeyVaultUri'
          value: ''
        }
        {
          name: 'KeyVaultUri'
          value: ''
        }
        {
          name: 'Completion:Label'
          value: 'Completion'
        }
        {
          name: 'Completion:AIService'
          value: 'AzureOpenAI'
        }
        {
          name: 'Completion:DeploymentOrModelId'
          value: 'gpt-35-turbo'
        }
        {
          name: 'Completion:Endpoint'
          value: endpoint
        }
        {
          name: 'Completion:Key'
          value: apiKey
        }
        {
          name: 'Embedding:Label'
          value: 'Embedding'
        }
        {
          name: 'Embedding:AIService'
          value: 'AzureOpenAI'
        }
        {
          name: 'Embedding:DeploymentOrModelId'
          value: 'text-embedding-ada-002'
        }
        {
          name: 'Embedding:Endpoint'
          value: endpoint
        }
        {
          name: 'Embedding:Key'
          value: apiKey
        }
        {
          name: 'AzureSpeech:Region'
          value: ''
        }
        {
          name: 'AzureSpeech:Key'
          value: ''
        }
        {
          name: 'Authorization:Type'
          value: 'None'
        }
        {
          name: 'Authorization:ApiKey'
          value: ''
        }
        {
          name: 'Authorization:AzureAd:Instance'
#disable-next-line no-hardcoded-env-urls // This is just a default value
          value: 'https://login.microsoftonline.com/'
        }
        {
          name: 'Authorization:AzureAd:TenantId'
          value: ''
        }
        {
          name: 'Authorization:AzureAd:ClientId'
          value: ''
        }
        {
          name: 'Authorization:AzureAd:Scopes'
          value: 'access_as_user'
        }
        {
          name: 'ChatStore:Type'
          value: 'volatile'
        }
        {
          name: 'ChatStore:Filesystem'
          value: './data/chatstore.json'
        }
        {
          name: 'MemoriesStore:Type'
          value: 'volatile'
        }
        {
          name: 'DocumentMemory:GlobalDocumentCollectionName'
          value: 'global-documents'
        }
        {
          name: 'DocumentMemory:UserDocumentCollectionNamePrefix'
          value: 'user-documents-'
        }
        {
          name: 'DocumentMemory:DocumentLineSplitMaxTokens'
          value: '30'
        }
        {
          name: 'DocumentMemory:DocumentParagraphSplitMaxLines'
          value: '100'
        }
        {
          name: 'DocumentMemory:FileSizeLimit'
          value: '1000000'
        }
        {
          name: 'Planner:MaxTokens'
          value: '1024'
        }
        {
          name: 'Planner:RelevancyThreshold'
          value: '0.78'
        }
        {
          name: 'AllowedHosts'
          value: '*'
        }
        {
          name: 'BotSchema:Name'
          value: 'CopilotChat'
        }
        {
          name: 'BotSchema:Version'
          value: '1'
        }
        {
          name: 'Kestrel:Endpoints:Https:Url'
          value: 'https://localhost:443'
        }
        {
          name: 'Logging:LogLevel:Default'
          value: 'Warning'
        }
        {
          name: 'Logging:LogLevel:Microsoft.SemanticKernel'
          value: 'Warning'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsights.properties.InstrumentationKey
        }
      ]
    }
  }
  dependsOn: [
    logAnalyticsWorkspace
  ]
}

resource appServiceWebDeploy 'Microsoft.Web/sites/extensions@2021-03-01' = {
  name: 'MSDeploy'
  kind: 'string'
  parent: appServiceWeb
  properties: {
    packageUri: packageUri
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${uniqueName}-appi'
  location: location
  kind: 'string'
  tags: {
    displayName: 'AppInsight'
  }
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
  }
}

resource appInsightExtension 'Microsoft.Web/sites/siteextensions@2020-06-01' = {
  parent: appServiceWeb
  name: 'Microsoft.ApplicationInsights.AzureWebSites'
  dependsOn: [
    appInsights
  ]
}

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2020-08-01' = {
  name: '${uniqueName}-la'
  location: location
  tags: {
    displayName: 'Log Analytics'
  }
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 90
    features: {
      searchVersion: 1
      legacy: 0
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

output deployedUrl string = appServiceWeb.properties.defaultHostName

/*
Copyright (c) Microsoft. All rights reserved.
Licensed under the MIT license. See LICENSE file in the project root for full license information.

Bicep template for deploying Semantic Kernel to Azure as a web app service.

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


@description('Region for the resources')
#disable-next-line no-loc-expr-outside-params // We force the location to be the same as the resource group's for a simpler,
var location = resourceGroup().location       // more intelligible deployment experience at the cost of some flexibility

@description('Name for the deployment - Made unique')
var uniqueName = '${name}-${uniqueString(resourceGroup().id)}'


resource openAI 'Microsoft.CognitiveServices/accounts@2022-03-01' = {
  name: 'ai-${uniqueName}'
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: toLower(uniqueName)
  }
}

resource openAI_gpt35Turbo 'Microsoft.CognitiveServices/accounts/deployments@2022-12-01' = {
  parent: openAI
  name: 'gpt-35-turbo'
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-35-turbo'
      version: '0301'
    }
    scaleSettings: {
      scaleType: 'Standard'
    }
  }
}

resource openAI_textEmbeddingAda002 'Microsoft.CognitiveServices/accounts/deployments@2022-12-01' = {
  parent: openAI
  name: 'text-embedding-ada-002'
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-ada-002'
      version: '1'
    }
    scaleSettings: {
      scaleType: 'Standard'
    }
  }
  dependsOn: [        // This "dependency" is to create models sequentially because the resource
    openAI_gpt35Turbo // provider does not support parallel creation of models properly.
  ]
}

resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: 'asp-${uniqueName}'
  location: location
  sku: {
    name: appServiceSku
  }
}

resource appServiceWeb 'Microsoft.Web/sites@2022-03-01' = {
  name: 'app-${uniqueName}skweb'
  location: location
  tags: {
    skweb: '1'
  }
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
          name: 'Completion:AIService'
          value: 'AzureOpenAI'
        }
        {
          name: 'Completion:Endpoint'
          value: openAI.properties.endpoint
        }
        {
          name: 'Completion:Key'
          value: openAI.listKeys().key1
        }
        {
          name: 'Embedding:AIService'
          value: 'AzureOpenAI'
        }
        {
          name: 'Embedding:Endpoint'
          value: openAI.properties.endpoint
        }
        {
          name: 'Embedding:Key'
          value: openAI.listKeys().key1
        }
        {
          name: 'Planner:AIService'
          value: 'AzureOpenAI'
        }
        {
          name: 'Planner:Endpoint'
          value: openAI.properties.endpoint
        }
        {
          name: 'Planner:Key'
          value: openAI.listKeys().key1
        }
        {
          name: 'ChatStore:Type'
          value: 'volatile'
        }
        {
          name: 'MemoriesStore:Type'
          value: 'volatile'
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
          name: 'Logging:LogLevel:SemanticKernel.Service'
          value: 'Warning'
        }
        {
          name: 'Logging:LogLevel:Microsoft.SemanticKernel'
          value: 'Warning'
        }
        {
          name: 'Logging:LogLevel:Microsoft.AspNetCore.Hosting'
          value: 'Warning'
        }
        {
          name: 'Logging:LogLevel:Microsoft.Hosting.Lifetimel'
          value: 'Warning'
        }
        {
          name: 'ApplicationInsights:ConnectionString'
          value: appInsights.properties.ConnectionString
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
  name: 'appi-${uniqueName}'
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
  name: 'la-${uniqueName}'
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

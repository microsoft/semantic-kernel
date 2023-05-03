/*
Copyright (c) Microsoft. All rights reserved.
Licensed under the MIT license. See LICENSE file in the project root for full license information.

Bicep template for deploying Semantic Kernel to Azure as a web app service without creating a new Azure OpenAI instance.

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

@description('Underlying AI service')
@allowed([
  'AzureOpenAI'
  'OpenAI'
])
param aiService string = 'AzureOpenAI'

@description('Model to use for chat completions')
param completionModel string = 'gpt-35-turbo'

@description('Model to use for text embeddings')
param embeddingModel string = 'text-embedding-ada-002'

@description('Completion model the task planner should use')
param plannerModel string = 'gpt-35-turbo'

@description('Azure OpenAI endpoint to use (ignored when AI service is not AzureOpenAI)')
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
          value: aiService
        }
        {
          name: 'Completion:DeploymentOrModelId'
          value: completionModel
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
          name: 'Embedding:AIService'
          value: aiService
        }
        {
          name: 'Embedding:DeploymentOrModelId'
          value: embeddingModel
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
          name: 'Planner:AIService'
          value: aiService
        }
        {
          name: 'Planner:DeploymentOrModelId'
          value: plannerModel
        }
        {
          name: 'Planner:Endpoint'
          value: endpoint
        }
        {
          name: 'Planner:Key'
          value: apiKey
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

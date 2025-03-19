targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment that can be used as part of naming resource convention')
param environmentName string

@description('The current user ID, to assign RBAC permissions to')
param currentUserId string

// Main deployment parameters
param prefix string = 'copstsk'
@minLength(1)
@description('Primary location for all resources')
param location string

@minLength(1)
@description('Name of the Azure OpenAI resource')
param openAIName string

@minLength(1)
@description('Name of the Azure Resource Group where the OpenAI resource is located')
param openAIResourceGroupName string

@description('Azure Bot app ID')
param botAppId string
@description('Azure Bot app password')
@secure()
param botPassword string
@description('Azure Bot tenant ID')
param botTenantId string

param openAIModel string
param openAIApiVersion string
param apiAppExists bool = false
param runningOnGh string = ''

var tags = {
  'azd-env-name': environmentName
}

resource rg 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  name: 'rg-${environmentName}'
  location: location
  tags: tags
}

var uniqueId = uniqueString(rg.id)
var principalType = empty(runningOnGh) ? 'User' : 'ServicePrincipal'

module uami './uami.bicep' = {
  name: 'uami'
  scope: rg
  params: {
    uniqueId: uniqueId
    prefix: prefix
    location: location
  }
}

module appin './appin.bicep' = {
  name: 'appin'
  scope: rg
  params: {
    uniqueId: uniqueId
    prefix: prefix
    location: location
    userAssignedIdentityPrincipalId: uami.outputs.principalId
  }
}

module acrModule './acr.bicep' = {
  name: 'acr'
  scope: rg
  params: {
    uniqueId: uniqueId
    prefix: prefix
    userAssignedIdentityPrincipalId: uami.outputs.principalId
    location: location
  }
}

module openAI './openAI.bicep' = {
  name: 'openAI'
  scope: resourceGroup(openAIResourceGroupName)
  params: {
    openAIName: openAIName
    userAssignedIdentityPrincipalId: uami.outputs.principalId
  }
}

module aca './aca.bicep' = {
  name: 'aca'
  scope: rg
  params: {
    uniqueId: uniqueId
    prefix: prefix
    userAssignedIdentityResourceId: uami.outputs.identityId
    containerRegistry: acrModule.outputs.acrName
    location: location
    logAnalyticsWorkspaceName: appin.outputs.logAnalyticsWorkspaceName
    applicationInsightsConnectionString: appin.outputs.applicationInsightsConnectionString
    openAiApiKey: '' // Force ManId, otherwise set openAI.listKeys().key1
    openAiEndpoint: openAI.outputs.openAIEndpoint
    openAiModel: openAIModel
    openAiApiVersion: openAIApiVersion
    userAssignedIdentityClientId: uami.outputs.clientId
    apiAppExists: apiAppExists
    botAppId: botAppId
    botPassword: botPassword
    botTenantId: botTenantId
  }
}

module bot 'bot.bicep' = {
  name: 'bot'
  scope: rg
  params: {
    uniqueId: uniqueId
    prefix: prefix
    botAppId: botAppId
    botTenantId: botTenantId
    messagesEndpoint: aca.outputs.messagesEndpoint
  }
}

// These outputs are copied by azd to .azure/<env name>/.env file
// post provision script will use these values, too
output AZURE_RESOURCE_GROUP string = rg.name
output APPLICATIONINSIGHTS_CONNECTIONSTRING string = appin.outputs.applicationInsightsConnectionString
output AZURE_TENANT_ID string = subscription().tenantId
output AZURE_USER_ASSIGNED_IDENTITY_ID string = uami.outputs.identityId
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = acrModule.outputs.acrEndpoint
output AZURE_OPENAI_MODEL string = openAIModel
output AZURE_OPENAI_ENDPOINT string = openAI.outputs.openAIEndpoint
output AZURE_OPENAI_API_VERSION string = openAIApiVersion
output ENDPOINT_URL string = aca.outputs.messagesEndpoint
output MANIFEST_URL string = aca.outputs.manifestUrl
output HOME_URL string = aca.outputs.homeUrl
output BOT_APP_ID string = botAppId
output BOT_TENANT_ID string = botTenantId

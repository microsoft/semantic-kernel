param uniqueId string
param prefix string
param userAssignedIdentityResourceId string
param userAssignedIdentityClientId string
param openAiEndpoint string
param openAiApiKey string
param openAiApiVersion string = '2024-08-01-preview'
param openAiModel string = 'gpt-4o'
param applicationInsightsConnectionString string
param containerRegistry string = '${prefix}acr${uniqueId}'
param location string = resourceGroup().location
param logAnalyticsWorkspaceName string
param apiAppExists bool
param emptyContainerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
param botAppId string
@secure()
param botPassword string
param botTenantId string

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: logAnalyticsWorkspaceName
}

// see https://azureossd.github.io/2023/01/03/Using-Managed-Identity-and-Bicep-to-pull-images-with-Azure-Container-Apps/
resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-11-02-preview' = {
  name: '${prefix}-containerAppEnv-${uniqueId}'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityResourceId}': {}
    }
  }
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
  }
}

// When azd passes parameters, it will tell if apps were already created
// In this case, we don't overwrite the existing image
// See https://johnnyreilly.com/using-azd-for-faster-incremental-azure-container-app-deployments-in-azure-devops#the-does-your-service-exist-parameter
module fetchLatestImageApi './fetch-container-image.bicep' = {
  name: 'api-app-image'
  params: {
    exists: apiAppExists
    name: '${prefix}-api-${uniqueId}'
  }
}

resource apiContainerApp 'Microsoft.App/containerApps@2023-11-02-preview' = {
  name: '${prefix}-api-${uniqueId}'
  location: location
  tags: { 'azd-service-name': 'api' }
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityResourceId}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 80
        transport: 'auto'
      }
      registries: [
        {
          server: '${containerRegistry}.azurecr.io'
          identity: userAssignedIdentityResourceId
        }
      ]
    }
    template: {
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
      containers: [
        {
          name: 'api'
          image: apiAppExists ? fetchLatestImageApi.outputs.containers[0].image : emptyContainerImage
          resources: {
            cpu: 1
            memory: '2Gi'
          }
          env: [
            { name: 'AZURE_CLIENT_ID', value: userAssignedIdentityClientId }
            { name: 'BOT_APP_ID', value: botAppId }
            { name: 'BOT_PASSWORD', value: botPassword }
            { name: 'BOT_TENANT_ID', value: botTenantId }
            { name: 'APPLICATIONINSIGHTS_CONNECTIONSTRING', value: applicationInsightsConnectionString }
            { name: 'APPLICATIONINSIGHTS_SERVICE_NAME', value: 'api' }
            { name: 'AZURE_OPENAI_ENDPOINT', value: openAiEndpoint }
            { name: 'AZURE_OPENAI_CHAT_DEPLOYMENT_NAME', value: openAiModel }
            { name: 'AZURE_OPENAI_API_KEY', value: '' }
            { name: 'AZURE_OPENAI_API_VERSION', value: openAiApiVersion }
          ]
        }
      ]
    }
  }
}

output messagesEndpoint string = 'https://${apiContainerApp.properties.configuration.ingress.fqdn}/api/messages'
output manifestUrl string = 'https://${apiContainerApp.properties.configuration.ingress.fqdn}/manifest'
output homeUrl string = 'https://${apiContainerApp.properties.configuration.ingress.fqdn}'

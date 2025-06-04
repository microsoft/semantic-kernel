param uniqueId string
param prefix string
param userAssignedIdentityPrincipalId string
param acrName string = '${prefix}acr${uniqueId}'
param location string = resourceGroup().location

resource acr 'Microsoft.ContainerRegistry/registries@2021-06-01-preview' = {
  name: acrName
  location: location
  sku: {
    name: 'Standard' // Choose between Basic, Standard, and Premium based on your needs
  }
  properties: {
    adminUserEnabled: false
  }
}

resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(acr.id, userAssignedIdentityPrincipalId, 'acrpull')
  scope: acr
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // Role definition ID for AcrPull
    principalId: userAssignedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

output acrName string = acrName
output acrEndpoint string = acr.properties.loginServer

targetScope = 'resourceGroup'

param openAIName string
param userAssignedIdentityPrincipalId string

resource openAI 'Microsoft.CognitiveServices/accounts@2022-03-01' existing = {
  name: openAIName
}

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(openAI.id, userAssignedIdentityPrincipalId, 'Cognitive Services OpenAI User')
  scope: openAI
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd') // Role definition ID for Cognitive Services OpenAI User
    principalId: userAssignedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

output openAIEndpoint string = openAI.properties.endpoint

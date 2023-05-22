/*
Copyright (c) Microsoft. All rights reserved.
Licensed under the MIT license. See LICENSE file in the project root for full license information.

Bicep template for deploying Semantic Kernel to Azure as a web app service with a new Azure OpenAI account.
*/

@description('Name for the deployment - Must consist of alphanumeric characters or \'-\'')
param name string = 'semkernel'

@description('SKU for the Azure App Service plan')
@allowed(['B1', 'S1', 'S2', 'S3', 'P1V3', 'P2V3', 'I1V2', 'I2V2' ])
param appServiceSku string = 'B1'

@description('Location of package to deploy as the web service')
#disable-next-line no-hardcoded-env-urls // This is an arbitrary package URI
param packageUri string = 'https://skaasdeploy.blob.core.windows.net/api/semantickernelapi.zip'

@description('Model to use for chat completions')
param completionModel string = 'gpt-35-turbo'

@description('Model to use for text embeddings')
param embeddingModel string = 'text-embedding-ada-002'

@description('Completion model the task planner should use')
param plannerModel string = 'gpt-35-turbo'

@description('Semantic Kernel server API key - Generated GUID by default\nProvide empty string to disable API key auth')
param semanticKernelApiKey string = newGuid()

@description('Whether to deploy Cosmos DB for chat storage')
param deployCosmosDB bool = true

// TODO: Temporarily disabling qdrant deployment by default while we secure its endpoint.
@description('Whether to deploy Qdrant (in a container) for memory storage')
param deployQdrant bool = false

@description('Whether to deploy Azure Speech Services to be able to input chat text by voice')
param deploySpeechServices bool = true


module openAI 'main.bicep' = {
  name: 'openAIDeployment'
  params: {
    name: name
    appServiceSku: appServiceSku
    packageUri: packageUri
    aiService: 'AzureOpenAI'
    completionModel: completionModel
    embeddingModel: embeddingModel
    plannerModel: plannerModel
    semanticKernelApiKey: semanticKernelApiKey
    deployCosmosDB: deployCosmosDB
    deployQdrant: deployQdrant
    deploySpeechServices: deploySpeechServices
    deployNewAzureOpenAI: true
  }
}

output endpoint string = openAI.outputs.deployedUrl

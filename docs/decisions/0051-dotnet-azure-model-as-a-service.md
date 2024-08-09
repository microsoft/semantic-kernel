---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: rogerbarreto
date: 2024-08-07
deciders: rogerbarreto, markwallace-microsoft
consulted: taochen
---

# Support Connector for .Net Azure Model-as-a-Service (Azure AI Studio)

## Context and Problem Statement

There has been a demand from customers to use and support natively models deployed in [Azure AI Studio - Serverless APIs](https://learn.microsoft.com/en-us/azure/ai-studio/how-to/model-catalog-overview#model-deployment-managed-compute-and-serverless-api-pay-as-you-go), This mode of consumption operates on a pay-as-you-go basis, typically using tokens for billing purposes. Clients can access the service via the [Azure AI Model Inference API](https://learn.microsoft.com/en-us/azure/ai-studio/reference/reference-model-inference-api?tabs=azure-studio) or client SDKs.

At present, there is no official support for [Azure AI Studio](https://learn.microsoft.com/en-us/azure/ai-studio/what-is-ai-studio). The purpose of this ADR is to examine the constraints of the service and explore potential solutions to enable support for the service via the development of a new AI connector.

## Azure Inference Client library for .NET

The Azure team has a new client library, namely [Azure.AI.Inference](https://github.com/Azure/azure-sdk-for-net/blob/Azure.AI.Inference_1.0.0-beta.1/sdk/ai/Azure.AI.Inference/README.md) in .Net, for effectively interacting with the service. While the service API is OpenAI-compatible, it is not permissible to use the OpenAI and the Azure OpenAI client libraries for interacting with the service as they are not independent with respect to both the models and their providers. This is because Azure AI Studio features a diverse range of open-source models, other than OpenAI models.

### Limitations

Currently is known that the first version of the client SDK will only support: `Chat Completion` and `Text Embedding Generation` and `Image Embedding Generation` with `TextToImage Generation` planned.

There are no current plans to support `Text Generation` modality.

## AI Connector

### Namespace options

- `Microsoft.SemanticKernel.Connectors.AzureAI`
- `Microsoft.SemanticKernel.Connectors.AzureAIInference`
- `Microsoft.SemanticKernel.Connectors.AzureAIModelInference`

Decision: `Microsoft.SemanticKernel.Connectors.AzureAIInference`

### Support for model-specific parameters

Models can possess supplementary parameters that are not part of the default API. The service API and the client SDK enable the provision of model-specific parameters. Users can provide model-specific settings via a dedicated argument along with other settings, such as `temperature` and `top_p`, among others.

Azure AI Inference specialized `PromptExecutionSettings`, will support those customizable parameters.

### Feature Branch

The development of the Azure AI Inference connector will be done in a feature branch named `feature-connectors-azureaiinference`.

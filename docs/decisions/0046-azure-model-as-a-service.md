---
# These are optional elements. Feel free to remove any of them.
status: { accepted }
contact: { rogerbarreto, taochen }
date: { 2024-06-20 }
deciders: { alliscode, moonbox3, eavanvalkenburg }
consulted: {}
informed: {}
---

# Support for Azure Model-as-a-Service in SK

## Context and Problem Statement

There has been a demand from customers for the implementation of Model-as-a-Service (MaaS) in SK. MaaS, which is also referred to as [serverless API](https://learn.microsoft.com/en-us/azure/ai-studio/how-to/model-catalog-overview#model-deployment-managed-compute-and-serverless-api-pay-as-you-go), is available in [Azure AI Studio](https://learn.microsoft.com/en-us/azure/ai-studio/what-is-ai-studio). This mode of consumption operates on a pay-as-you-go basis, typically using tokens for billing purposes. Clients can access the service via the [Azure AI Model Inference API](https://learn.microsoft.com/en-us/azure/ai-studio/reference/reference-model-inference-api?tabs=azure-studio) or client SDKs.

At present, there is no official support for MaaS in SK. The purpose of this ADR is to examine the constraints of the service and explore potential solutions to enable support for the service in SK via the development of a new AI connector.

## Client SDK

The Azure team will be providing a new client library, namely `Azure.AI.Inference` in .Net and `azure-ai-inference` in Python, for effectively interacting with the service. While the service API is OpenAI-compatible, it is not permissible to use the OpenAI and the Azure OpenAI client libraries for interacting with the service as they are not independent with respect to both the models and their providers. This is because Azure AI Studio features a diverse range of open-source models, other than OpenAI models.

### Limitations

The initial release of the client SDK will only support chat completion and text/image embedding generation, with image generation to be added later.

Plans to support for text completion are currently unclear, and it is highly unlikely that the SDK will ever include support for text completion. As a result, the new AI connector will **NOT** support text completions in the initial version until we get more customer signals or the client SDK adds support.

## AI Connector

### Naming options

- Azure
- AzureAI
- AzureAIInference
- AzureAIModelInference

  Decision: `AzureAIInference`

### Support for model-specific parameters

Models can possess supplementary parameters that are not part of the default API. The service API and the client SDK enable the provision of model-specific parameters. Users can provide model-specific settings via a dedicated argument along with other settings, such as `temperature` and `top_p`, among others.

In the context of SK, execution parameters are categorized under `PromptExecutionSettings`, which is inherited by all connector-specific setting classes. The settings of the new connector will contain a member of type `dictionary`, which will group together the model-specific parameters.

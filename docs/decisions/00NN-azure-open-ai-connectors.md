---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: rogerbarreto
date: 2024-06-10
deciders: rogerbarreto, matthewbolanos, markwallace-microsoft
---

# OpenAI and Azure Connectors Naming and Structuring

## Context and Problem Statement

It has recently been announced that OpenAI and Azure will each have their own dedicated SDKs for accessing their services. Previously, there was no official SDK for OpenAI, and our OpenAI Connector relied solely on the Azure SDK client for access.

With the introduction of the official OpenAI SDK, we now have access to more up-to-date features provided by OpenAI, making it advantageous to use this SDK instead of the Azure SDK.

Additionally, it has become clear that we need to separate the OpenAI connector into two distinct targets: one for OpenAI and another for Azure OpenAI. This separation will enhance code clarity and facilitate a better understanding of the usage of each target.

### OpenAI SDK limitations

The new OpenAI SDK has some limitations that need to be considered and will introduce breaking changes to the current OpenAI connector regardless of the chosen option below.

OpenAI SDK limitations:

- ⚠️ No support for multiple results (Choices) per request.
- ⚠️ Text Generation modality is not supported.

### OpenAI CELA Restrictions

`OpenAIChatCompletion` services using custom endpoints (For Ollama, LMStudio and OpenAI compatible engines) cannot be used with OpenAI SDK internally due to CELA restrictions and a new `CustomClient` (Similar to the one in HuggingFace) will need to added as a shared internal utility to be used by any other connector supporting custom OpenAI compatible endpoints.

This is a problem that will need to be addressed by all options below.

## Decision Drivers

- Avoiding breaking changes whenever possible.
- Develop a new dedicated connector for Azure OpenAI, utilizing the underlying Azure SDK.
- Minimize or eliminate any breaking changes for developers currently using the existing OpenAI connector.

## Considered Options

- Option 1 - Azure OpenAI Connector + Obsolete Azure references in OpenAI connector.
- Option 2 - Current OpenAI Connector changing internals only.

## Option 1 - Azure OpenAI Connector + Break Azure references in OpenAI connector

This option will create a new connector for Azure OpenAI and the current OpenAI connector will be updated to use the new OpenAI SDK.

The new Azure OpenAI connector will be created in a new namespace with similar Azure APIs to access the Azure OpenAI services.

The SemanticKernel meta package will be updated to automatically include also the new `Azure.OpenAI` connector.

Impact:

- `Azure` extension methods will be removed from `SemanticKernel.Connectors.OpenAI` namespace to avoid clash with same names introduced in the new `SemanticKernel.Connectors.Azure.OpenAI`.
- `AzureOpenAIChatCompletion` and `AzureOpenAITextGeneration` services will be obsoleted and throw not supported exceptions when used from `SemanticKernel.Connectors.OpenAI` namespace.

### Azure Namespace Changes

After some discussions the understanding ideal would be to have a new namespace `Connectors.Azure` root naming dedicated for Azure specific Connectors like: `Azure.AISearch`, `Azure.OpenAI`, `Azure.CosmosDB`, `Azure.InferenceAI(Maas)` etc.

Starting with the `SemanticKernel.Connectors.Azure.OpenAI` namespace to host the new Azure OpenAI connector.

Pros:

- Clear separation of concerns between OpenAI and Azure OpenAI connectors.
- No breaking changes for developers using the current OpenAI connector.

Cons:

- Breaking changes for developers using the current OpenAI connector.
- Breaking changes upcomming for developers using the current Azure specific connectors (AI + Memory).

## Option 2 - Current OpenAI Connector changing internals only

This option is fully focused in the least impact possible, combining both Azure and OpenAI SDK dependencies in one single connector as it currently is.

1. Update the current OpenAI specific services and client to use new OpenAI SDK
2. Update Azure specific services and client to use the latest Azure OpenAI SDK.

Pros:

- No breaking changes for developers using the current OpenAI connector.

Cons:

- The footprint of the connector will increase due to the inclusion of both SDKs as dependencies.
- Might not be possible to use the latest Open AI SDK updated versions due to version conflicts with Azure SDK, making us tied to the Azure SDK deployment schedule defeating the purpose of up-to-date OpenAI features.

## Decision Outcome

Chosen option: TBD

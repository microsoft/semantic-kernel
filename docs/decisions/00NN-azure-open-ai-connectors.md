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

## Decision Drivers

- Avoiding breaking changes whenever possible.
- Develop a new dedicated connector for Azure OpenAI, utilizing the underlying Azure SDK.
- Minimize or eliminate any breaking changes for developers currently using the existing OpenAI connector.

## Considered Options

- Option 1 - Azure OpenAI Connector + Obsolete Azure references in OpenAI connector.
- Option 2 - Current OpenAI Connector changing internals only.

## Versioning

This new package will avoid major breaking changes and the versioning will follow the minor changes, increasing the 1.x version number when the connectors are updated

## Upgrade Path

A documentation page will be created to guide developers on how to upgrade from the current OpenAI connector to the new version when needed.

## Option 1 - Keep OpenAI as is + Add new OpenAI SDK

This is the least impactiful approach where we keep the current OpenAI connector APIs using last Azure SDK `1.0.0-beta.17` and update the new Open AI APIs using the new Open AI 2.0-beta SDK.

A new connector will be created for Azure OpenAI services, using the Azure SDK 2.0-beta and new APIs using the configuration approach will be created.

The new API's are going to use a `Options` pattern to configure its details and we will take the benefit of this new change to avoid any clashing with the current OpenAI connector and new Azure OpenAI connector.

Pros:

- Minimal breaking changes for developers using the current OpenAI connector.
- Clear separation of concerns between OpenAI and Azure OpenAI connectors.

Cons:

- Added dependency for both `Azure OpenAI 1.0-beta17` and `OpenAI 2.0-beta1`.

## Option 2 - Azure OpenAI Connector + Break Azure references in OpenAI connector

This option will create a new connector for Azure OpenAI and the current OpenAI connector will be updated to use the new OpenAI SDK.

The new Azure OpenAI connector will be created in a new namespace with similar Azure APIs to access the Azure OpenAI services.

The SemanticKernel meta package will be updated to automatically include also the new `Azure.OpenAI` connector.

Impact:

- `Azure` extension methods will be removed from `SemanticKernel.Connectors.OpenAI` namespace to avoid clash with same names introduced in the new `SemanticKernel.Connectors.AzureOpenAI`.

- `AzureOpenAIChatCompletion` and `AzureOpenAITextGeneration` services will be obsoleted and throw not supported exceptions when used from `SemanticKernel.Connectors.OpenAI` namespace.

Pros:

- Clear separation of concerns between OpenAI and Azure OpenAI connectors.
- No breaking changes for developers using the current OpenAI connector.

Cons:

- Breaking changes for developers using the current OpenAI connector.
- Breaking changes upcomming for developers using the current Azure specific connectors (AI + Memory).

## Option 3 - Current OpenAI Connector changing internals only

This option is fully focused in the least impact possible, combining both Azure and OpenAI SDK dependencies in one single connector as it currently is.

1. Update the current OpenAI specific services and client to use new OpenAI SDK
2. Update Azure specific services and client to use the latest Azure OpenAI SDK.

Pros:

- No breaking changes for developers using the current OpenAI connector.

Cons:

- The footprint of the connector will increase due to the inclusion of both SDKs as dependencies.
- Might not be possible to use the latest Open AI SDK updated versions due to version conflicts with Azure SDK, making us tied to the Azure SDK deployment schedule defeating the purpose of up-to-date OpenAI features.

## Decision Outcome

Chosen option: Option 1 - Keep OpenAI as is + Add new OpenAI SDK

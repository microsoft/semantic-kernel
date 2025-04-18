## Overview

Three intent-triage agents are provided:

1. [`IntentTriageAgent1`](./IntentTriageAgent1.cs): 

    - Explicitly orchestrates tool invocation and response logic and is not susceptible to model specific behavior inconsistencies across different models.
    - Based on tools defined in the [`LanguagePlugin`](./Tools/LanguagePlugin.cs).
    - Exhibits significantly less latency when producing a result.
    - [`IntentTriageAgent1`](./IntentTriageAgent1.cs) is a subclass of [`ServiceAgent`](../Service/ServiceAgent.cs)
      
1. [`IntentTriageAgent2`](./IntentTriageAgent2.cs): 
  
    - Relies on the LLM's tool calling abilities and instruction prompt and requires considerably less code.
    - Based on tools defined in the [`LanguagePlugin`](./Tools/LanguagePlugin.cs).
    - Bound to the latency of the associated LLM
    - [`IntentTriageAgent2`](./IntentTriageAgent2.cs) is a subclass of [`ComposedServiceAgent`](../Service/ComposedServiceAgent.cs)
      
1. [`IntentTriageAgent3`](./IntentTriageAgent3.cs): 
  
    - Uses OpenAPI spec and instructions from original demo.
    - Relies on the model's ability to form requests to the language service.
    - Exhibits high token usage and sporadic failed requests (bad request).
    - [`IntentTriageAgent3`](./IntentTriageAgent3.cs) is a subclass of [`ComposedServiceAgent`](../Service/ComposedServiceAgent.cs)

[`LanguagePlugin`](./Tools/LanguagePlugin.cs) adapts the raw API into a simplified contract for the model to call.
This simplification addresses both the _input_ data model as well as the _response_ data model.
Registering the OpenAPI tool directly the model would result in high token consumption.

[`LanguagePlugin`](./Tools/LanguagePlugin.cs) also relies on explicit result parsing to avoid
defining an explicit object model.

Both functions in the [`LanguagePlugin`](./Tools/LanguagePlugin.cs) will filter results based on a confidence threshold.
While one might expect the model to be able to handle this, the presence of low confidence
results do tend to influence the model response and generative LLM doesn't excel at quantitative analysis. 
(see: [How Many R’s in the Word “Strawberry?”](https://medium.com/@SamMormando/how-many-rs-in-the-word-strawberry-a6b8a697a1be))

While a reasoning model might exhibit more reliable behavior, requiring the use of a reasoning model
is likely not enforceble for every use of the agent.


## Configuration

Both agents rely upon the same configurations scheme:

Key|Settings|Description|
---|---|---
clu.projectName|[`IntentTriageLanguageSettings`](./IntentTriageLanguageSettings.cs)|The project name for the CLU model.
clu.deploymentName|[`IntentTriageLanguageSettings`](./IntentTriageLanguageSettings.cs)|The deployment name for the CLU model.
cqa.projectName|[`IntentTriageLanguageSettings`](./IntentTriageLanguageSettings.cs)|The project name for the CQA model.
cqa.deploymentName|[`IntentTriageLanguageSettings`](./IntentTriageLanguageSettings.cs)|The deployment name for the CQA model.
language.resourceUrl|[`IntentTriageLanguageSettings`](./IntentTriageLanguageSettings.cs)|The base url (scheme + host) for the language services endpoint
language.resourceKey|[`IntentTriageLanguageSettings`](./IntentTriageLanguageSettings.cs)|The api key for the language services
language.resourceVersion|[`IntentTriageLanguageSettings`](./IntentTriageLanguageSettings.cs)|The api version for the language services
foundry:connectionstring|[`FoundrySettings`](../Service/FoundrySettings.cs)|A connection string to the Foundry project hosting the agent
foundry:deploymentname|[`FoundrySettings`](../Service/FoundrySettings.cs)|The name of the model deployment for the Azure OpenAI service

These may be defined as dotnet user-secrets using the following script:

```bsh
dotnet user-secrets set "clu.projectName" "<value>"
dotnet user-secrets set "clu.deploymentName" "<value>"
dotnet user-secrets set "cqa.projectName" "<value>"
dotnet user-secrets set "cqa.deploymentName" "<value>"
dotnet user-secrets set "language.resourceUrl" "<value>"
dotnet user-secrets set "language.resourceKey" "<value>"
dotnet user-secrets set "language.resourceVersion" "<value>"

dotnet user-secrets set "foundry:connectionstring" "<value>"
dotnet user-secrets set "foundry:deploymentname" "gpt-4o-mini"
```

## Running

Both agents can be executed in the [`Step03_IntentTriage`](../../../../samples/GettingStartedWithAgents/ServiceAgents/Step03_IntentTriage.cs) sample.

> Manually change the types on lines 41 & 43 of the `Step03_IntentTriage` to control which agent is used.

Test have two modes and each mode invoked streaming and non-streaming results.

1. Developer mode: Simulates the developer experience (not catalog hosted) as if they referenced the agent package as a project dependency.
1. Hosted mode: Simulates a service hosted agent that is instantiated via the [`ServiceAgentProviderFactory`](../Service/ServiceAgentProviderFactory.cs)
   and the associated [`ServiceAgentProvider`](../Service/ServiceAgentProvider.cs)

> The most expedient test is `UseAgentAsDeveloperAsync`



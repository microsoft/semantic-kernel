---
# These are optional elements. Feel free to remove any of them.
status: proposed
date: 2023-08-15
deciders: shawncal
consulted:
informed:
---
# Dynamic payload building for PUT and POST RestAPI operations and parameter namespacing

## Context and Problem Statement
Currently, the SK OpenAPI does not allow the dynamic creation of payload/body for PUT and POST RestAPI operations, even though all the required metadata is available. One of the reasons the functionality was not fully developed originally, and eventually removed is that JSON payload/body content of PUT and POST RestAPI operations might contain properties with identical names at various levels. It was not clear how to unambiguously resolve their values from the flat list of context variables. Another reason the functionality has not been added yet is that the 'payload' context variable, along with RestAPI operation data contract schema(OpenAPI, JSON schema, Typings?) should have been sufficient for LLM to provide fully fleshed-out JSON payload/body content without the need to build it dynamically.

<!-- This is an optional element. Feel free to remove. -->
## Decision Drivers
* Create a mechanism that enables the dynamic construction of the payload/body for PUT and POST RestAPI operations.
* Develop a mechanism(namespacing) that allows differentiation of payload properties with identical names at various levels for PUT and POST RestAPI operations.
* Aim to minimize breaking changes and maintain backward compatibility of the code as much as possible.

## Considered Options
* Enable the dynamic creation of payload and/or namespacing by default.
* Enable the dynamic creation of payload and/or namespacing based on configuration.

## Decision Outcome
Chosen option: "Enable the dynamic creation of payload and/or namespacing based on configuration". This option keeps things compatible, so the change won't affect any SK consumer code. Additionally, it lets SK consumer code easily control both mechanisms, turning them on or off based on the scenario.

## Additional details

### Enabling dynamic creation of payload
In order to enable the dynamic creation of payloads/bodies for PUT and POST RestAPI operations, please set the `EnableDynamicPayload` property of the `OpenApiSkillExecutionParameters` execution parameters to `true` when importing the AI plugin:

```csharp
var plugin = await kernel.ImportPluginFunctionsAsync("<skill name>", new Uri("<chatGPT-plugin>"), new OpenApiSkillExecutionParameters(httpClient) { EnableDynamicPayload = true });
```

To dynamically construct a payload for a RestAPI operation that requires payload like this:
```json
{
	"value": "secret-value",
	"attributes": {
		"enabled": true
	}
}
```

Please register the following arguments in context variables collection:

```csharp
var contextVariables = new ContextVariables();
contextVariables.Set("value", "secret-value");
contextVariables.Set("enabled", true);
```

### Enabling namespacing
To enable namespacing, set the `EnablePayloadNamespacing` property of the `OpenApiSkillExecutionParameters` execution parameters to `true` when importing the AI plugin:

```csharp
var plugin = await kernel.ImportPluginFunctionsAsync("<skill name>", new Uri("<chatGPT-plugin>"), new OpenApiSkillExecutionParameters(httpClient) { EnablePayloadNamespacing = true });
```
Remember that the namespacing mechanism depends on prefixing parameter names with their parent parameter name, separated by dots. So, use the 'namespaced' parameter names when adding arguments for them to the context variables. Let's consider this JSON:

```json
{ 
  "upn": "<sender upn>", 
  "receiver": {
    "upn": "<receiver upn>"
  },
  "cc": {
    "upn": "<cc upn>"
  }
}
```
It contains `upn` properties at different levels. The the argument registration for the parameters(property values) will look like:
```csharp
var contextVariables = new ContextVariables();
contextVariables.Set("upn", "<sender-upn-value>");
contextVariables.Set("receiver.upn", "<receiver-upn-value>");
contextVariables.Set("cc.upn", "<cc-upn-value>");
```

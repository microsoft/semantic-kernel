---
status: accepted
contact: gitri-ms
date: 2023-09-21
deciders: gitri-ms, shawncal
consulted: lemillermicrosoft, awharrison-28, dmytrostruk, nacharya1
informed: eavanvalkenburg, kevdome3000
---
# OpenAI Function Calling Support

## Context and Problem Statement

The [function calling](https://platform.openai.com/docs/guides/gpt/function-calling) capability of OpenAI's Chat Completions API allows developers to describe functions to the model, and have the model decide whether to output a JSON object specifying a function and appropriate arguments to call in response to the given prompt.  This capability is enabled by two new API parameters to the `/v1/chat/completions` endpoint:
- `function_call` - auto (default), none, or a specific function to call
- `functions` - JSON descriptions of the functions available to the model

Functions provided to the model are injected as part of the system message and are billed/counted as input tokens.

We have received several community requests to provide support for this capability when using SK with the OpenAI chat completion models that support it.

## Decision Drivers

* Minimize changes to the core kernel for OpenAI-specific functionality
* Cost concerns with including a long list of function descriptions in the request
* Security and cost concerns with automatically executing functions returned by the model

## Considered Options

* Support sending/receiving functions via chat completions endpoint _with_ modifications to interfaces
* Support sending/receiving functions via chat completions endpoint _without_ modifications to interfaces
* Implement a planner around the function calling capability

## Decision Outcome

Chosen option: "Support sending/receiving functions via chat completions endpoint _without_ modifications to interfaces"

With this option, we utilize the existing request settings object to send functions to the model. The app developer controls what functions are included and is responsible for validating and executing the function result.

### Consequences

* Good, because avoids breaking changes to the core kernel
* Good, because OpenAI-specific functionality is contained to the OpenAI connector package
* Good, because allows app to control what functions are available to the model (including non-SK functions)
* Good, because keeps the option open for integrating with planners in the future
* Neutral, because requires app developer to validate and execute resulting function
* Bad, because not as obvious how to use this capability and access the function results

## Pros and Cons of the Options

### Support sending/receiving functions _with_ modifications to chat completions interfaces

This option would update the `IChatCompletion` and `IChatResult` interfaces to expose parameters/methods for providing and accessing function information. 

* Good, because provides a clear path for using the function calling capability
* Good, because allows app to control what functions are available to the model (including non-SK functions)
* Neutral, because requires app developer to validate and execute resulting function
* Bad, because introduces breaking changes to core kernel abstractions
* Bad, because OpenAI-specific functionality would be included in core kernel abstractions and would need to be ignored by other model providers

### Implement a planner around the function calling capability

Orchestrating external function calls fits within SK's concept of planning.  With this approach, we would implement a planner that would take the function calling result and produce a plan that the app developer could execute (similar to SK's ActionPlanner).

* Good, because producing a plan result makes it easy for the app developer to execute the chosen function
* Bad, because functions would need to be registered with the kernel in order to be executed
* Bad, because would create confusion about when to use which planner

## Additional notes
There has been much discussion and debate over the pros and cons of automatically invoking a function returned by the OpenAI model, if it is registered with the kernel. As there are still many open questions around this behavior and its implications, we have decided to not include this capability in the initial implementation.  We will continue to explore this option and may include it in a future update.
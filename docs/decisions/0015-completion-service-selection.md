---
# These are optional elements. Feel free to remove any of them.
status: accepted
date: 2023-10-25
deciders: markwallace, mabolan
consulted:
informed:
---
# Completion service type selection strategy

## Context and Problem Statement
Today, SK runs all text prompts using the text completion service. With the addition of a new chat completion prompts and potentially other prompt types, such as image, on the horizon, we need a way to select a completion service type to run these prompts.

<!-- This is an optional element. Feel free to remove. -->
## Decision Drivers
* Semantic function should be able to identify a completion service type to use when processing text, chat, or image prompts.

## Considered Options
**1. Completion service type identified by the "prompt_type" property.** This option presumes adding the 'prompt_type' property to the prompt template config model class, 'PromptTemplateConfig.' The property will be specified once by a prompt developer and will be used by the 'SemanticFunction' class to decide which completion service type (not instance) to use when resolving an instance of that particular completion service type.

**Prompt template**
```json
{
    "schema": "1",
    "description": "Hello AI, what can you do for me?",
    "prompt_type": "<text|chat|image>",
    "models": [...]
}
```

**Semantic function pseudocode**
```csharp
if(string.IsNullOrEmpty(promptTemplateConfig.PromptType) || promptTemplateConfig.PromptType == "text")
{
    var service = this._serviceSelector.SelectAIService<ITextCompletion>(context.ServiceProvider, this._modelSettings);
    //render the prompt, call the service, process and return result
} 
else (promptTemplateConfig.PromptType == "chat")
{
    var service = this._serviceSelector.SelectAIService<IChatCompletion>(context.ServiceProvider, this._modelSettings);
    //render the prompt, call the service, process and return result
},
else (promptTemplateConfig.PromptType == "image")
{
    var service = this._serviceSelector.SelectAIService<IImageGeneration>(context.ServiceProvider, this._modelSettings);
    //render the prompt, call the service, process and return result
}
```

**Example**

```json
name: ComicStrip.Create
prompt: "Generate ideas for a comic strip based on {{$input}}. Design characters, develop the plot, ..."
config: {
	"schema": 1,
	"prompt_type": "text",
	...
}

name: ComicStrip.Draw
prompt: "Draw the comic strip - {{$comicStrip.Create $input}}"
config: {
	"schema": 1,
	"prompt_type": "image",
	...
}
```

Pros:
 - Deterministically specifies which completion service **type** to use, so image prompts won't be rendered by a text completion service, and vice versa.

Cons:
 - Another property to specify by a prompt developer.



**2. Completion service type identified by prompt content.** The idea behind this option is to analyze the rendered prompt by using regex to check for the presence of specific markers associated with the prompt type. For example, the presence of the `<message role="*"></message>` tag in the rendered prompt might indicate that the prompt is a chat prompt and should be handled by the chat completion service. This approach may work reliably when we have two completion service types - text and chat - since the logic would be straightforward: if the message tag is found in the rendered prompt, handle it with the chat completion service; otherwise, use the text completion service. However, this logic becomes unreliable when we start adding new prompt types, and those prompts lack markers specific to their prompt type. For example, if we add an image prompt, we won't be able to distinguish between a text prompt and an image prompt unless the image prompt has a unique marker identifying it as such.

```csharp
if (Regex.IsMatch(renderedPrompt, @"<message>.*?</message>"))
{
    var service = this._serviceSelector.SelectAIService<IChatCompletion>(context.ServiceProvider, this._modelSettings);
    //render the prompt, call the service, process and return result
},
else
{
    var service = this._serviceSelector.SelectAIService<ITextCompletion>(context.ServiceProvider, this._modelSettings);
    //render the prompt, call the service, process and return result
}
```

**Example**

```json
name: ComicStrip.Create
prompt: "Generate ideas for a comic strip based on {{$input}}. Design characters, develop the plot, ..."
config: {
	"schema": 1,
	...
}

name: ComicStrip.Draw
prompt: "Draw the comic strip - {{$comicStrip.Create $input}}"
config: {
	"schema": 1,
	...
}
```
Pros:
- No need for a new property to identify the prompt type.

Cons:
- Unreliable unless the prompt contains unique markers specifically identifying the prompt type.

## Decision Outcome
We decided to choose the '2. Completion service type identified by prompt content' option and will reconsider it when we encounter another completion service type that cannot be supported by this option or when we have a solid set of requirements for using a different mechanism for selecting the completion service type.

---
# These are optional elements. Feel free to remove any of them.
status: accepted
contact: sergeymenshykh
date: 2024-04-17
deciders: markwallace, matthewbolanos, rbarreto, dmytrostruk
consulted: 
informed:
---

# Function Call Content

## Context and Problem Statement

Today, in SK, LLM function calling is supported exclusively by the OpenAI connector, and the function calling model is specific to that connector. At the time of writing the ARD, two new connectors are being added that support function calling, each with its own specific model for function calling. The design, in which each new connector introduces its own specific model class for function calling, does not scale well from the connector development perspective and does not allow for polymorphic use of connectors by SK consumer code.

Another scenario in which it would be beneficial to have an LLM/service-agnostic function calling model classes is to enable agents to pass function calls to one another. In this situation, an agent using the OpenAI Assistant API connector/LLM may pass the function call content/request/model for execution to another agent that build on top of the OpenAI chat completion API.

This ADR describes the high-level details of the service-agnostic function-calling model classes, while leaving the low-level details to the implementation phase. Additionally, this ADR outlines the identified options for various aspects of the design.

Requirements - https://github.com/microsoft/semantic-kernel/issues/5153

## Decision Drivers
1. Connectors should communicate LLM function calls to the connector callers using service-agnostic function model classes.
2. Consumers should be able to communicate function results back to connectors using service-agnostic function model classes.  
3. All existing function calling behavior should still work.  
4. It should be possible to use service-agnostic function model classes without relying on the OpenAI package or any other LLM-specific one.  
5. It should be possible to serialize a chat history object with function call and result classes so it can be rehydrated in the future (and potentially run the chat history with a different AI model).  
6. It should be possible to pass function calls between agents. In multi-agent scenarios, one agent can create a function call for another agent to complete it.  
7. It should be possible to simulate a function call. A developer should be able to add a chat message with a function call they created to a chat history object and then run it with any LLM (this may require simulating function call IDs in the case of OpenAI).

## 1. Service-agnostic function call model classes
Today, SK relies on connector specific content classes to communicate LLM intent to call function(s) to the SK connector caller:
```csharp
IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

ChatHistory chatHistory = new ChatHistory();
chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

// The OpenAIChatMessageContent class is specific to OpenAI connectors - OpenAIChatCompletionService, AzureOpenAIChatCompletionService.
OpenAIChatMessageContent result = (OpenAIChatMessageContent)await chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

// The ChatCompletionsFunctionToolCall belongs Azure.AI.OpenAI package that is OpenAI specific.
List<ChatCompletionsFunctionToolCall> toolCalls = result.ToolCalls.OfType<ChatCompletionsFunctionToolCall>().ToList();

chatHistory.Add(result);
foreach (ChatCompletionsFunctionToolCall toolCall in toolCalls)
{
    string content = kernel.Plugins.TryGetFunctionAndArguments(toolCall, out KernelFunction? function, out KernelArguments? arguments) ?
        JsonSerializer.Serialize((await function.InvokeAsync(kernel, arguments)).GetValue<object>()) :
        "Unable to find function. Please try again!";

    chatHistory.Add(new ChatMessageContent(
        AuthorRole.Tool,
        content,
        metadata: new Dictionary<string, object?>(1) { { OpenAIChatMessageContent.ToolIdProperty, toolCall.Id } }));
}
```

Both `OpenAIChatMessageContent` and `ChatCompletionsFunctionToolCall` classes are OpenAI-specific and cannot be used by non-OpenAI connectors. Moreover, using the LLM vendor-specific classes complicates the connector's caller code and makes it impossible to work with connectors polymorphically - referencing a connector through the `IChatCompletionService` interface while being able to swap its implementations.

To address this issues, we need a mechanism that allows communication of LLM intent to call functions to the caller and returning function call results back to LLM in a service-agnostic manner. Additionally, this mechanism should be extensible enough to support potential multi-modal cases when LLM requests function calls and returns other content types in a single response.

Considering that the SK chat completion model classes already support multi-modal scenarios through the `ChatMessageContent.Items` collection, this collection can also be leveraged for function calling scenarios. Connectors would need to map LLM function calls to service-agnostic function content model classes and add them to the items collection. Meanwhile, connector callers would execute the functions and communicate the execution results back through the items collection as well.

A few options for the service-agnostic function content model classes are being considered below.

### Option 1.1 - FunctionCallContent to represent both function call (request) and function result  
This option assumes having one service-agnostic model class - `FunctionCallContent` to communicate both function call and function result:
```csharp
class FunctionCallContent : KernelContent
{
    public string? Id {get; private set;}
    public string? PluginName {get; private set;}
    public string FunctionName {get; private set;}
    public KernelArguments? Arguments {get; private set; }
    public object?/FunctionResult/string? Result {get; private set;} // The type of the property is being described below.
    
    public string GetFullyQualifiedName(string functionNameSeparator = "-") {...}

    public Task<FunctionResult> InvokeAsync(Kernel kernel, CancellationToken cancellationToken = default)
    {
        // 1. Search for the plugin/function in kernel.Plugins collection.
        // 2. Create KernelArguments by deserializing Arguments.
        // 3. Invoke the function.
    }
}
```

**Pros**:
- One model class to represent both function call and function result.

**Cons**:
- Connectors will need to determine whether the content represents a function call or a function result by analyzing the role of the parent `ChatMessageContent` in the chat history, as the type itself does not convey its purpose.  
  * This may not be a con at all because a protocol defining a specific role (AuthorRole.Tool?) for chat messages to pass function results to connectors will be required. Details are discussed below in this ADR.

### Option 1.2 - FunctionCallContent to represent a function call and FunctionResultContent to represent the function result
This option proposes having two model classes - `FunctionCallContent` for communicating function calls to connector callers:
```csharp
class FunctionCallContent : KernelContent
{
    public string? Id {get;}
    public string? PluginName {get;}
    public string FunctionName {get;}
    public KernelArguments? Arguments {get;}
    public Exception? Exception {get; init;}

    public Task<FunctionResultContent> InvokeAsync(Kernel kernel,CancellationToken cancellationToken = default)
    {
        // 1. Search for the plugin/function in kernel.Plugins collection.
        // 2. Create KernelArguments by deserializing Arguments.
        // 3. Invoke the function.
    }

    public static IEnumerable<FunctionCallContent> GetFunctionCalls(ChatMessageContent messageContent)
    {
        // Returns list of function calls provided via <see cref="ChatMessageContent.Items"/> collection.
    }
}
```

and - `FunctionResultContent` for communicating function results back to connectors:
```csharp
class FunctionResultContent : KernelContent
{
    public string? Id {get; private set;}
    public string? PluginName {get; private set;}
    public string? FunctionName {get; private set;}

    public object?/FunctionResult/string? Result {get; set;}

    public ChatMessageContent ToChatMessage()
    {
        // Creates <see cref="ChatMessageContent"/> and adds the current instance of the class to the <see cref="ChatMessageContent.Items"/> collection.
    }
}
```

**Pros**:
- The explicit model, compared to the previous option, allows the caller to clearly declare the intent of the content, regardless of the role of the parent `ChatMessageContent` message.  
  * Similar to the drawback for the option above, this may not be an advantage because the protocol defining the role of chat message to pass the function result to the connector will be required.

**Cons**:
- One extra content class.

### The connector caller code example:
```csharp
//The GetChatMessageContentAsync method returns only one choice. However, there is a GetChatMessageContentsAsync method that can return multiple choices.
ChatMessageContent messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);
chatHistory.Add(messageContent); // Adding original chat message content containing function call(s) to the chat history

IEnumerable<FunctionCallContent> functionCalls = FunctionCallContent.GetFunctionCalls(messageContent); // Getting list of function calls.
// Alternatively: IEnumerable<FunctionCallContent> functionCalls = messageContent.Items.OfType<FunctionCallContent>();

// Iterating over the requested function calls and invoking them.
foreach (FunctionCallContent functionCall in functionCalls)
{
    FunctionResultContent? result = null;

    try
    {
        result = await functionCall.InvokeAsync(kernel); // Resolving the function call in the `Kernel.Plugins` collection and invoking it.
    }
    catch(Exception ex)
    {
        chatHistory.Add(new FunctionResultContent(functionCall, ex).ToChatMessage());
        // or
        //string message = "Error details that LLM can reason about.";
        //chatHistory.Add(new FunctionResultContent(functionCall, message).ToChatMessageContent());
        
        continue;
    }
    
    chatHistory.Add(result.ToChatMessage());
    // or chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection() { result }));
}

// Sending chat history containing function calls and function results to the LLM to get the final response
messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);
```

The design does not require callers to create an instance of chat message for each function result content. Instead, it allows multiple instances of the function result content to be sent to the connector through a single instance of chat message:
```csharp
ChatMessageContent messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);
chatHistory.Add(messageContent); // Adding original chat message content containing function call(s) to the chat history.

IEnumerable<FunctionCallContent> functionCalls = FunctionCallContent.GetFunctionCalls(messageContent); // Getting list of function calls.

ChatMessageContentItemCollection items = new ChatMessageContentItemCollection();

// Iterating over the requested function calls and invoking them
foreach (FunctionCallContent functionCall in functionCalls)
{
    FunctionResultContent result = await functionCall.InvokeAsync(kernel);

    items.Add(result);
}

chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, items);

// Sending chat history containing function calls and function results to the LLM to get the final response
messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);
```

### Decision Outcome
Option 1.2 was chosen due to its explicit nature.

## 2. Function calling protocol for chat completion connectors
Different chat completion connectors may communicate function calls to the caller and expect function results to be sent back via messages with a connector-specific role. For example, the `{Azure}OpenAIChatCompletionService` connectors use messages with an `Assistant` role to communicate function calls to the connector caller and expect the caller to return function results via messages with a `Tool` role.  
   
The role of a function call message returned by a connector is not important to the caller, as the list of functions can easily be obtained by calling the `GetFunctionCalls` method, regardless of the role of the response message.

```csharp
ChatMessageContent messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

IEnumerable<FunctionCallContent> functionCalls = FunctionCallContent.GetFunctionCalls(); // Will return list of function calls regardless of the role of the messageContent if the content contains the function calls.
```

However, having only one connector-agnostic role for messages to send the function result back to the connector is important for polymorphic usage of connectors. This would allow callers to write code like this:

 ```csharp
 ...
IEnumerable<FunctionCallContent> functionCalls = FunctionCallContent.GetFunctionCalls();

foreach (FunctionCallContent functionCall in functionCalls)
{
    FunctionResultContent result = await functionCall.InvokeAsync(kernel);

    chatHistory.Add(result.ToChatMessage());
}
...
```

and avoid code like this:

```csharp
IChatCompletionService chatCompletionService = new();
...
IEnumerable<FunctionCallContent> functionCalls = FunctionCallContent.GetFunctionCalls();

foreach (FunctionCallContent functionCall in functionCalls)
{
    FunctionResultContent result = await functionCall.InvokeAsync(kernel);

    // Using connector-specific roles instead of a single connector-agnostic one to send results back to the connector would prevent the polymorphic usage of connectors and force callers to write if/else blocks.
    if(chatCompletionService is OpenAIChatCompletionService || chatCompletionService is AzureOpenAIChatCompletionService)
    {
        chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection() { result });
    }
    else if(chatCompletionService is AnotherCompletionService)
    {
        chatHistory.Add(new ChatMessageContent(AuthorRole.Function, new ChatMessageContentItemCollection() { result });
    }
    else if(chatCompletionService is SomeOtherCompletionService)
    {
        chatHistory.Add(new ChatMessageContent(AuthorRole.ServiceSpecificRole, new ChatMessageContentItemCollection() { result });
    }
}
...
```

### Decision Outcome
It was decided to go with the `AuthorRole.Tool` role because it is well-known, and conceptually, it can represent function results as well as any other tools that SK will need to support in the future.

## 3. Type of FunctionResultContent.Result property:
There are a few data types that can be used for the `FunctionResultContent.Result` property. The data type in question should allow the following scenarios:  
- Be serializable/deserializable, so that it's possible to serialize chat history containing function result content and rehydrate it later when needed.  
- It should be possible to communicate function execution failure either by sending the original exception or a string describing the problem to LLM.  
   
So far, three potential data types have been identified: object, string, and FunctionResult.

### Option 3.1 - object
```csharp
class FunctionResultContent : KernelContent
{
    // Other members are omitted
    public object? Result {get; set;}
}
```

This option may require the use of JSON converters/resolvers for the {de}serialization of chat history, which contains function results represented by types not supported by JsonSerializer by default.

**Pros**:
- Serialization is performed by the connector, but it can also be done by the caller if necessary.
- The caller can provide additional data, along with the function result, if needed.
- The caller has control over how to communicate function execution failure: either by passing an instance of an Exception class or by providing a string description of the problem to LLM.

**Cons**:


### Option 3.2 - string (current implementation)
```csharp
class FunctionResultContent : KernelContent
{
    // Other members are omitted
    public string? Result {get; set;}
}
```
**Pros**:
- No convertors are required for chat history {de}serialization.
- The caller can provide additional data, along with the function result, if needed.
- The caller has control over how to communicate function execution failure: either by passing serialized exception, its message or by providing a string description of the problem to LLM.

**Cons**:
- Serialization is performed by the caller. It can be problematic for polymorphic usage of chat completion service.

### Option 3.3 - FunctionResult
```csharp
class FunctionResultContent : KernelContent
{
    // Other members are omitted
    public FunctionResult? Result {get;set;}

    public Exception? Exception {get;set}
    or 
    public object? Error { get; set; } // Can contain either an instance of an Exception class or a string describing the problem.
}
```
**Pros**:
- Usage of FunctionResult SK domain class.

**Cons**:
- It is not possible to communicate an exception to the connector/LLM without the additional Exception/Error property.  
- `FunctionResult` is not {de}serializable today:
  * The `FunctionResult.ValueType` property has a `Type` type that is not serializable by JsonSerializer by default, as it is considered dangerous.  
  * The same applies to `KernelReturnParameterMetadata.ParameterType` and `KernelParameterMetadata.ParameterType` properties of type `Type`.  
  * The `FunctionResult.Function` property is not deserializable and should be marked with the [JsonIgnore] attribute.  
    * A new constructor, ctr(object? value = null, IReadOnlyDictionary<string, object?>? metadata = null), needs to be added for deserialization. 
    * The `FunctionResult.Function` property has to be nullable. It can be a breaking change? for the function filter users because the filters use `FunctionFilterContext` class that expose an instance of kernel function via the `Function` property.

### Option 3.4 - FunctionResult: KernelContent
Note: This option was suggested during a second round of review of this ADR.
   
This option suggests making the `FunctionResult` class a derivative of the `KernelContent` class:
```csharp
public class FunctionResult : KernelContent
{
    ....
}
```
So, instead of having a separate `FunctionResultContent` class to represent the function result content, the `FunctionResult` class will inherit from the `KernelContent` class, becoming the content itself. As a result, the function result returned by the `KernelFunction.InvokeAsync` method can be directly added to the `ChatMessageContent.Items` collection:
```csharp
foreach (FunctionCallContent functionCall in functionCalls)
{
    FunctionResult result = await functionCall.InvokeAsync(kernel);

    chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection { result }));
    // instead of
    chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection { new FunctionResultContent(functionCall, result) }));
    
    // of cause, the syntax can be simplified by having additional instance/extension methods
    chatHistory.AddFunctionResultMessage(result); // Using the new AddFunctionResultMessage extension method of ChatHistory class
}
```

Questions:
- How to pass the original `FunctionCallContent` to connectors along with the function result. It's actually not clear atm whether it's needed or not. The current rationale is that some models might expect properties of the original function call, such as arguments, to be passed back to the LLM along with the function result. An argument can be made that the original function call can be found in the chat history by the connector if needed. However, a counterargument is that it may not always be possible because the chat history might be truncated to save tokens, reduce hallucination, etc.
- How to pass function id to connector?
- How to communicate exception to the connectors? It was proposed to add the `Exception` property the the `FunctionResult` class that will always be assigned by the `KernelFunction.InvokeAsync` method. However, this change will break C# function calling semantic, where the function should be executed if the contract is satisfied, or an exception should be thrown if the contract is not fulfilled.
- If `FunctionResult` becomes a non-steaming content by inheriting `KernelContent` class, how the `FunctionResult` can represent streaming content capabilities represented by the `StreamingKernelContent` class when/if it needed later? C# does not support multiple inheritance.

**Pros**
- The `FunctionResult` class becomes a content(non-streaming one) itself and can be passed to all the places where content is expected.
- No need for the extra `FunctionResultContent` class .
  
**Cons**
- Unnecessarily coupling between the `FunctionResult` and `KernelContent` classes might be a limiting factor preventing each one from evolving independently as they otherwise could.
- The `FunctionResult.Function` property needs to be changed to nullable in order to be serializable, or custom serialization must be applied to {de}serialize the function schema without the function instance itself.  
- The `Id` property should be added to the `FunctionResult` class to represent the function ID required by LLMs.
- 
### Decision Outcome
Originally, it was decided to go with Option 3.1 because it's the most flexible one comparing to the other two. In case a connector needs to get function schema, it can easily be obtained from kernel.Plugins collection available to the connector. The function result metadata can be passed to the connector through the `KernelContent.Metadata` property.
However, during the second round of review for this ADR, Option 3.4 was suggested for exploration. Finally, after prototyping Option 3.4, it was decided to return to Option 3.1 due to the cons of Option 3.4.

## 4. Simulated functions
There are cases when LLM ignores data provided in the prompt due to the model's training. However, the model can work with the same data if it is provided to the model via a function result.  
   
There are a few ways the simulated function can be modeled:

### Option 4.1 - Simulated function as SemanticFunction
```csharp
...

ChatMessageContent messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

// Simulated function call
FunctionCallContent simulatedFunctionCall = new FunctionCallContent(name: "weather-alert", id: "call_123");
messageContent.Items.Add(simulatedFunctionCall); // Adding a simulated function call to the connector response message

chatHistory.Add(messageContent);

// Creating SK function and invoking it
KernelFunction simulatedFunction = KernelFunctionFactory.CreateFromMethod(() => "A Tornado Watch has been issued, with potential for severe ..... Stay informed and follow safety instructions from authorities.");
FunctionResult simulatedFunctionResult = await simulatedFunction.InvokeAsync(kernel);

chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection() { new FunctionResultContent(simulatedFunctionCall, simulatedFunctionResult) }));

messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

...
```
**Pros**:
- SK function filters/hooks can be triggered when the caller invoke the simulated function.
 
**Cons**:
- Not as light-weight as the other option.

### Option 4.2 - object as simulated function
```csharp
...

ChatMessageContent messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

// Simulated function
FunctionCallContent simulatedFunctionCall = new FunctionCallContent(name: "weather-alert", id: "call_123");
messageContent.Items.Add(simulatedFunctionCall);

chatHistory.Add(messageContent);

// Creating simulated result
string simulatedFunctionResult = "A Tornado Watch has been issued, with potential for severe ..... Stay informed and follow safety instructions from authorities."

//or

WeatherAlert simulatedFunctionResult = new WeatherAlert { Id = "34SD7RTYE4", Text = "A Tornado Watch has been issued, with potential for severe ..... Stay informed and follow safety instructions from authorities." };

chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection() { new FunctionResultContent(simulatedFunctionCall, simulatedFunctionResult) }));

messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

...
```
**Pros**:
- A lighter option comparing to the previous one because no SK function creation and execution required.

**Cons**:
- SK function filters/hooks can't be triggered when the caller invoke the simulated function.

### Decision Outcome
The provided options are not mutually exclusive; each can be used depending on the scenario.

## 5. Streaming
The design of a service-agnostic function calling model for connectors' streaming API should be similar to the non-streaming one described above.
  
The streaming API differs from a non-streaming one in that the content is returned in chunks rather than all at once. For instance, OpenAI connectors currently return function calls in two chunks: the function id and name come in the first chunk, while the function arguments are sent in subsequent chunks. Furthermore, LLM may stream function calls for more than one function in the same response. For example, the first chunk streamed by a connector may have the id and name of the first function, and the following chunk will have the id and name of the second function. 

This will require slight deviations in the design of the function-calling model for the streaming API to more naturally accommodate the streaming specifics. In the case of a significant deviation, a separate ADR will be created to outline the details.
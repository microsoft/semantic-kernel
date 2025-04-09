---
status: proposed
contact: sergeymenshykh
date: 2025-01-21
deciders: dmytrostruk, markwallace, rbarreto, sergeymenshykh, westey-m,
consulted: stephentoub
---

# Function Calling Reliability

## Context and Problem Statement
One key aspect of function calling, that determines the reliability of SK function calling, is the AI model's ability to call functions using the exact names with which they were advertised.

More often than wanted, the AI model hallucinates function names when calling them. In majority of cases, 
it's only one character in function name that is hallucinated, and the rest of the function name is correct. This character is the hyphen character `-` that 
SK uses as a separator between plugin name and function name to form the function fully qualified name (FQN) when advertising the function to uniquely identify 
functions across all plugins. For example, if the plugin name is `foo` and the function name is `bar`, the FQN of the function is `foo-bar`. The hallucinated names
seen so far are `foo_bar`, `foo.bar`.

### Issue #1: Underscore Separator Hallucination - `foo_bar`

When the AI model hallucinates the underscore separator `_`, SK detects this error and returns the message _"Error: Function call request for a function that wasn't defined."_ 
to the model as part of the function result, along with the original function call, in the subsequent request.
Some models can automatically recover from this error and call the function using the correct name, while others cannot.

### Issue #2: Dot Separator Hallucination - `foo.bar`

This issue is similar to the Issue #1, but in this case the separator is `.`. Although the SK detects this error and tries to return it to the AI model in the subsequent request, 
the request fails with the exception: _"Invalid messages[3].tool_calls[0].function.name: string does not match pattern. Expected a string that matches the pattern ^[a-zA-Z0-9_-]+$."_ 
The reason for this failure is that the hallucinated separator `.` is not permitted in the function name. Essentially, the model rejects the function name it hallucinated itself.

### Issue #3: Reliability of the Auto-Recovery Mechanism  
   
When a function is called using a name different from its advertised name, the function cannot be found, resulting in an error message being returned to the AI model, as described above.
This error message provides the AI model with a hint about the issue, helping it to auto-recover by calling the function using the correct name. 
However, the auto-recovery mechanism does not operate reliably across different models. 
For instance, it works with the `gpt-4o-mini(2024-07-18)` model but fails with the `gpt-4(0613)` and `gpt-4o(2024-08-06)` ones. 
When the AI model is unable to recover, it simply returns a variation of the error message: _"I'm sorry, but I can't provide the answer right now due to a system error. Please try again later."_   

## Decision Drivers

- Minimize the occurrence of function name hallucinations.
- Enhance the reliability of the auto-recovery mechanism.

## Considered Options
Some of the options are not mutually exclusive and can be combined.

### Option 1: Use Only Function Name for Function FQN

This option proposes using only the function name as function's FQN. For example, the FQN for the function `bar` from the plugin `foo` would simply be `bar`.
By using only the function name, we eliminate the need for the separator `-`, which is often hallucinated.

Pros:
- Reduces or eliminates function name hallucinations by removing the source of hallucination (Issues #1 and #2).
- Decreases the number of tokens consumed by the plugin name in the function FQN.

Cons:
- Function names may not be unique across all plugins. For instance, if two plugins have a function with the same name, both will be provided to the AI model, and SK will invoke the first function it encounters.
    - [From the ADR review meeting] If duplicates are found, the plugin name can be dynamically added to the duplicates or to all advertised functions.
- The lack of the plugin name may result in insufficient context for function names. For example, the function `GetData` has different meanings in the context of the `Weather` plugin compared to the `Stocks` plugin.
    - [From the ADR review meeting] The plugin name/context can be added to function names or descriptions by the plugin developer or automatically to the function descriptions by SK.
- It cannot address hallucinated function names. For instance, if the AI model hallucinates the function FQN `b0r` instead of `bar`.


Possible implementations:
```csharp
// Either at the operation level
FunctionChoiceBehaviorOptions options = new new()
{
    UseFunctionNameAsFqn = true
};

var settings = new AzureOpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options) };

var result = await this._chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, this._kernel);

// Or at the AI connector configuration level
IKernelBuilder builder = Kernel.CreateBuilder();
builder.AddOpenAIChatCompletion("<model-id>", "<api-key>", functionNamePolicy: FunctionNamePolicy.UseFunctionNameAsFqn);

// Or at the plugin level
string pluginName = string.Empty;

// If the plugin name is not an empty string, it will be used as the plugin name.   
// If it is null, then the plugin name will be inferred from the plugin type.   
// Otherwise, if the plugin name is an empty string, the plugin name will be omitted,   
// and all its functions will be advertised without a plugin name.  
kernel.ImportPluginFromType<Bar>(pluginName);
```


### Option 2: Custom Separator

This option proposes making the separator character, or a sequence of characters, configurable. Developers can specify a separator that is less likely to be mistakenly 
generated by the AI model. For example, they may choose `_` or `a1b` as the separator.

This solution may reduce the occurrences of function name hallucinations (Issues #1 and #2).

Pros:
- Reduces function name hallucinations by changing the separator to a less likely hallucinated character.

Cons:
- It won't work for cases when the separator is used in plugin name. For example the underscore symbol can be part of the `my_plugin` plugin name and also used as a separator, resulting in `my_plugin_myfunction` FQN.
    - [From the ADR review meeting] SK can dynamically remove any occurrences of the separator in plugin names and function names before advertising them.
- It can't address hallucinated function names. For instance, if the AI model generates the function FQN as `MyPlugin_my_func` instead of `MyPlugin_my_function`.

Possible implementations:
```csharp
// Either at the operation level
FunctionChoiceBehaviorOptions options = new new()
{
    FqnSeparator = "_"
};

var settings = new AzureOpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options) };

var result = await this._chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, this._kernel);

// Or at the AI connector configuration level
IKernelBuilder builder = Kernel.CreateBuilder();
builder.AddOpenAIChatCompletion("<model-id>", "<api-key>", functionNamePolicy: FunctionNamePolicy.Custom("_"));
```

### Option 3: No Separator  
   
This option proposes not using any separator between the plugin name and the function name. Instead, they will be concatenated directly.
For example, the FQN for the function `bar` from the plugin `foo` would be `foobar`.

Pros:
- Reduces function name hallucinations by eliminating the source of hallucination (Issues #1 and #2).

Cons:
- Requires a different function lookup heuristic.

### Option 4: Custom FQN Parser

This option proposes a custom, external FQN parser that can split function FQN into plugin name and function name. The parser will accepts the function FQN called by the AI model 
and returns both the plugin name and function name. To achieve this, the parser will attempt to parse the FQN using various separator characters:
```csharp
static (string? PluginName, string FunctionName) ParseFunctionFqn(ParseFunctionFqnContext context)
{
    static (string? PluginName, string FunctionName)? Parse(ParseFunctionFqnContext context, char separator)
    {
        string? pluginName = null;
        string functionName = context.FunctionFqn;

        int separatorPos = context.FunctionFqn.IndexOf(separator, StringComparison.Ordinal);
        if (separatorPos >= 0)
        {
            pluginName = context.FunctionFqn.AsSpan(0, separatorPos).Trim().ToString();
            functionName = context.FunctionFqn.AsSpan(separatorPos + 1).Trim().ToString();
        }

        // Check if the function registered in the kernel
        if (context.Kernel is { } kernel && kernel.Plugins.TryGetFunction(pluginName, functionName, out _))
        {
            return (pluginName, functionName);
        }

        return null;
    }

    // Try to use use hyphen, dot, and underscore sequentially as separators.
    var result = Parse(context, '-') ??
                    Parse(context, '.') ??
                    Parse(context, '_');

    if (result is not null)
    {
        return result.Value;
    }

    // If no separator is found, return the function name as is allowing AI connector to apply default behavior.
    return (null, context.FunctionFqn);
}
```

[From the ADR review meeting] Alternatively, the parser can return the function itself. This needs to be investigated further.
This [PR](https://github.com/microsoft/semantic-kernel/pull/10206) can provide more insights into how and where the parser is used.

Pros:
- It will mitigate but not reduce or completely eliminate function separator hallucinations by applying a custom heuristic specific to the AI model to parse the function FQN.
- It can be easily implemented in SK AI connectors.


Possible implementations:
```csharp
// Either at the operation level
static (string? PluginName, string FunctionName) ParseFunctionFqn(ParseFunctionFqnContext context)
{
    ...
}

FunctionChoiceBehaviorOptions options = new new()
{
    FqnParser = ParseFunctionFqn
};

var settings = new AzureOpenAIPromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options) };

var result = await this._chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, this._kernel);

// Or at the AI connector configuration level
IKernelBuilder builder = Kernel.CreateBuilder();
builder.AddOpenAIChatCompletion("<model-id>", "<api-key>", functionNamePolicy: FunctionNamePolicy.Custom("_", ParseFunctionFqn));
```

### Option 5: Improved Auto-Recovery Mechanism

Currently, when a function that was not advertised is called, SK returns the error message: _"Error: Function call request for a function that wasn't defined."_
Among the three AI models `gpt-4(0613)`, `gpt-4o-mini(2024-07-18)`, and `gpt-4o(2024-08-06)` only `gpt-4o-mini` can automatically recover from this error and successfully call the function using the correct name. 
The other two models fail to recover and instead return a final message similar to: _"I'm sorry, but I can't provide the answer right now due to a system error."_

However, by adding function name to the error message - "Error: Function call request for **foo.bar** function that wasn't defined." and 
the "You can call tools. If a tool call failed, correct yourself." system message to chat history, all three models can auto-recover from the error and call the function using the correct name.

Taking all this into account, we can add function name into the error message and provide recommendations to add the system message to improve the auto-recovery mechanism.

Pros:
- More models can auto-recover from the error.

Cons:
- The auto-recovery mechanism may not work for all AI models.

Possible implementation:
```csharp
// The caller code
 var chatHistory = new ChatHistory();
 chatHistory.AddSystemMessage("You can call tools. If a tool call failed, correct yourself.");
 chatHistory.AddUserMessage("<prompt>");


// In function calls processor
if (!checkIfFunctionAdvertised(functionCall))
{
    // errorMessage = "Error: Function call request for a function that wasn't defined.";
    errorMessage = $"Error: Function call request for the function that wasn't defined - {functionCall.FunctionName}.";
    return false;
}
```
 
### Option 6: Remove Disallowed Characters from the Function Name
   
This option proposes addressing Issue 2 by removing disallowed characters from the function FQN when returning the error message to the AI model.
This change will prevent the request to the AI model from failing with the exception: _"Invalid messages[3].tool_calls[0].function.name: string does not match pattern. Expected a string that matches the pattern `^[a-zA-Z0-9_-]+$`"_.
   
Pros:
- It will eliminate Issue 2 preventing AI model from auto-recovering from the error.
   

Possible implementation:
```csharp
// In AI connectors

var fqn = FunctionName.ToFullyQualifiedName(callRequest.FunctionName, callRequest.PluginName, OpenAIFunction.NameSeparator);

// Replace all disallowed characters with an underscore.
fqn = Regex.Replace(fqn, "[^a-zA-Z0-9_-]", "_");

toolCalls.Add(ChatToolCall.CreateFunctionToolCall(callRequest.Id, fqn, BinaryData.FromString(argument ?? string.Empty)));
```

## Decision Outcome
It was decided to start with the options that don't require changes to the public API surface - Options 5 and 6 and proceed with others later if needed, 
after evaluating the impact of the two applied options.
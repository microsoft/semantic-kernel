---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: dmytrostruk
date: 2024-09-10
deciders: sergeymenshykh, markwallace, rbarreto, westey-m, dmytrostruk, ben.thomas, evan.mattson, crickman
---

# Structured Outputs implementation in .NET version of Semantic Kernel

## Context and Problem Statement

[Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs) is a feature in OpenAI API that ensures the model will always generate responses based on provided JSON Schema. This gives more control over model responses, allows to avoid model hallucinations and write simpler prompts without a need to be specific about response format. This ADR describes several options how to enable this functionality in .NET version of Semantic Kernel.

A couple of examples how it's implemented in .NET and Python OpenAI SDKs:

.NET OpenAI SDK:
```csharp
ChatCompletionOptions options = new()
{
    ResponseFormat = ChatResponseFormat.CreateJsonSchemaFormat(
        name: "math_reasoning",
        jsonSchema: BinaryData.FromString("""
            {
                "type": "object",
                "properties": {
                "steps": {
                    "type": "array",
                    "items": {
                    "type": "object",
                    "properties": {
                        "explanation": { "type": "string" },
                        "output": { "type": "string" }
                    },
                    "required": ["explanation", "output"],
                    "additionalProperties": false
                    }
                },
                "final_answer": { "type": "string" }
                },
                "required": ["steps", "final_answer"],
                "additionalProperties": false
            }
            """),
    strictSchemaEnabled: true)
};

ChatCompletion chatCompletion = await client.CompleteChatAsync(
    ["How can I solve 8x + 7 = -23?"],
    options);

using JsonDocument structuredJson = JsonDocument.Parse(chatCompletion.ToString());

Console.WriteLine($"Final answer: {structuredJson.RootElement.GetProperty("final_answer").GetString()}");
Console.WriteLine("Reasoning steps:");
```

Python OpenAI SDK:

```python
class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

completion = client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[
        {"role": "system", "content": "Extract the event information."},
        {"role": "user", "content": "Alice and Bob are going to a science fair on Friday."},
    ],
    response_format=CalendarEvent,
)

event = completion.choices[0].message.parsed
```

## Considered Options

**Note**: All of the options presented in this ADR are not mutually exclusive - they can be implemented and supported simultaneously.

### Option #1: Use OpenAI.Chat.ChatResponseFormat object for ResponseFormat property (similar to .NET OpenAI SDK)

This approach means that `OpenAI.Chat.ChatResponseFormat` object with JSON Schema will be constructed by user and provided to `OpenAIPromptExecutionSettings.ResponseFormat` property, and Semantic Kernel will pass it to .NET OpenAI SDK as it is. 

Usage example:

```csharp
// Initialize Kernel
Kernel kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion(
        modelId: "gpt-4o-2024-08-06",
        apiKey: TestConfiguration.OpenAI.ApiKey)
    .Build();

// Create JSON Schema with desired response type from string.
ChatResponseFormat chatResponseFormat = ChatResponseFormat.CreateJsonSchemaFormat(
    name: "math_reasoning",
    jsonSchema: BinaryData.FromString("""
        {
            "type": "object",
            "properties": {
                "Steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "Explanation": { "type": "string" },
                            "Output": { "type": "string" }
                        },
                    "required": ["Explanation", "Output"],
                    "additionalProperties": false
                    }
                },
                "FinalAnswer": { "type": "string" }
            },
            "required": ["Steps", "FinalAnswer"],
            "additionalProperties": false
        }
        """),
    strictSchemaEnabled: true);

// Pass ChatResponseFormat in OpenAIPromptExecutionSettings.ResponseFormat property.
var executionSettings = new OpenAIPromptExecutionSettings
{
    ResponseFormat = chatResponseFormat
};

// Get string result.
var result = await kernel.InvokePromptAsync("How can I solve 8x + 7 = -23?", new(executionSettings));

Console.WriteLine(result.ToString());

// Output:

// {
//    "Steps":[
//       {
//          "Explanation":"Start with the equation: (8x + 7 = -23). The goal is to isolate (x) on one side of the equation. To begin, we need to remove the constant term from the left side of the equation.",
//          "Output":"8x + 7 = -23"
//       },
//       {
//          "Explanation":"Subtract 7 from both sides of the equation to eliminate the constant from the left side.",
//          "Output":"8x + 7 - 7 = -23 - 7"
//       },
//       {
//          "Explanation":"Simplify both sides: The +7 and -7 on the left will cancel out, while on the right side, -23 - 7 equals -30.",
//          "Output":"8x = -30"
//       },
//       {
//          "Explanation":"Now, solve for (x) by dividing both sides of the equation by 8. This will isolate (x).",
//          "Output":"8x / 8 = -30 / 8"
//       },
//       {
//          "Explanation":"Simplify the right side of the equation by performing the division: -30 divided by 8 equals -3.75.",
//          "Output":"x = -3.75"
//       }
//    ],
//    "FinalAnswer":"x = -3.75"
// }
```

Pros:
- This approach is already supported in Semantic Kernel without any additional changes, since there is a logic to pass `ChatResponseFormat` object as it is to .NET OpenAI SDK. 
- Consistent with .NET OpenAI SDK.

Cons:
- No type-safety. Information about response type should be manually constructed by user to perform a request. To access each response property, the response should be handled manually as well. It's possible to define a C# type and use JSON deserialization for response, but JSON Schema for request will still be defined separately, which means that information about the type will be stored in 2 places and any modifications to the type should be handled in 2 places.
- Inconsistent with Python version, where response type is defined in a class and passed to `response_format` property by simple assignment. 

### Option #2: Use C# type for ResponseFormat property (similar to Python OpenAI SDK)

This approach means that `OpenAI.Chat.ChatResponseFormat` object with JSON Schema will be constructed by Semantic Kernel, and user just needs to define C# type and assign it to `OpenAIPromptExecutionSettings.ResponseFormat` property.

Usage example:

```csharp
// Define desired response models
private sealed class MathReasoning
{
    public List<MathReasoningStep> Steps { get; set; }

    public string FinalAnswer { get; set; }
}

private sealed class MathReasoningStep
{
    public string Explanation { get; set; }

    public string Output { get; set; }
}

// Initialize Kernel
Kernel kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion(
        modelId: "gpt-4o-2024-08-06",
        apiKey: TestConfiguration.OpenAI.ApiKey)
    .Build();

// Pass desired response type in OpenAIPromptExecutionSettings.ResponseFormat property.
var executionSettings = new OpenAIPromptExecutionSettings
{
    ResponseFormat = typeof(MathReasoning)
};

// Get string result.
var result = await kernel.InvokePromptAsync("How can I solve 8x + 7 = -23?", new(executionSettings));

// Deserialize string to desired response type.
var mathReasoning = JsonSerializer.Deserialize<MathReasoning>(result.ToString())!;

OutputResult(mathReasoning);

// Output:

// Step #1
// Explanation: Start with the given equation.
// Output: 8x + 7 = -23

// Step #2
// Explanation: To isolate the term containing x, subtract 7 from both sides of the equation.
// Output: 8x + 7 - 7 = -23 - 7

// Step #3
// Explanation: To solve for x, divide both sides of the equation by 8, which is the coefficient of x.
// Output: (8x)/8 = (-30)/8

// Step #4
// Explanation: This simplifies to x = -3.75, as dividing -30 by 8 gives -3.75.
// Output: x = -3.75

// Final answer: x = -3.75
```

Pros:
- Type safety. Users won't need to define JSON Schema manually as it will be handled by Semantic Kernel, so users could focus on defining C# types only. Properties on C# type can be added or removed to change the format of desired response. `Description` attribute is supported to provide more detailed information about specific property.
- Consistent with Python OpenAI SDK.
- Minimal code changes are required since Semantic Kernel codebase already has a logic to build a JSON Schema from C# type.

Cons:
- Desired type should be provided via `ResponseFormat = typeof(MathReasoning)` or `ResponseFormat = object.GetType()` assignment, which can be improved by using C# generics.
- Response coming from Kernel is still a `string`, so it should be deserialized to desired type manually by user.

### Option #3: Use C# generics

This approach is similar to Option #2, but instead of providing type information via `ResponseFormat = typeof(MathReasoning)` or `ResponseFormat = object.GetType()` assignment, it will be possible to use C# generics.

Usage example:

```csharp
// Define desired response models
private sealed class MathReasoning
{
    public List<MathReasoningStep> Steps { get; set; }

    public string FinalAnswer { get; set; }
}

private sealed class MathReasoningStep
{
    public string Explanation { get; set; }

    public string Output { get; set; }
}

// Initialize Kernel
Kernel kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion(
        modelId: "gpt-4o-2024-08-06",
        apiKey: TestConfiguration.OpenAI.ApiKey)
    .Build();

// Get MathReasoning result.
var result = await kernel.InvokePromptAsync<MathReasoning>("How can I solve 8x + 7 = -23?");

OutputResult(mathReasoning);
```

Pros:
- Simple usage, no need in defining `PromptExecutionSettings` and deserializing string response later.

Cons:
- Implementation complexity compared to Option #1 and Option #2:
    1. Chat completion service returns a string, so deserialization logic should be added somewhere to return a type instead of string. Potential place: `FunctionResult`, as it already contains `GetValue<T>` generic method, but it doesn't contain deserialization logic, so it should be added and tested. 
    2. `IChatCompletionService` and its methods are not generic, but information about the response type should still be passed to OpenAI connector. One way would be to add generic version of `IChatCompletionService`, which may introduce a lot of additional code changes. Another way is to pass type information through `PromptExecutionSettings` object. Taking into account that `IChatCompletionService` uses `PromptExecutionSettings` and not `OpenAIPromptExecutionSettings`, `ResponseFormat` property should be moved to the base execution settings class, so it's possible to pass the information about response format without coupling to specific connector. On the other hand, it's not clear if `ResponseFormat` parameter will be useful for other AI connectors.
    3. Streaming scenario won't be supported, because for deserialization all the response content should be aggregated first. If Semantic Kernel will do the aggregation, then streaming capability will be lost.

## Out of scope

Function Calling functionality is out of scope of this ADR, since Structured Outputs feature is already partially used in current function calling implementation by providing JSON schema with information about function and its arguments. The only remaining parameter to add to this process is `strict` property which should be set to `true` to enable Structured Outputs in function calling. This parameter can be exposed through `PromptExecutionSettings` type. 

By setting `strict` property to `true` for function calling process, the model should not create additional non-existent parameters or functions, which could resolve hallucination problems. On the other hand, enabling Structured Outputs for function calling will introduce additional latency during first request since the schema is processed first, so it may impact the performance, which means that this property should be well-documented.

More information here: [Function calling with Structured Outputs](https://platform.openai.com/docs/guides/function-calling/function-calling-with-structured-outputs).

## Decision Outcome

1. Support Option #1 and Option #2, create a task for Option #3 to handle it separately. 
2. Create a task for Structured Outputs in Function Calling and handle it separately.

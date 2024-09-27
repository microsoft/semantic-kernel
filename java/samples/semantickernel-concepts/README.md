# Semantic Kernel Java Version Doc

The purpose of this article is to help you quickly grasp the key concepts in Semantic Kernel and get started quickly.

In Semantic Kernel Java, the **builder pattern** is extensively used. If you are not familiar with the builder pattern, I recommend you check out: [Builder Design Pattern](https://refactoring.guru/design-patterns/builder)

All the code examples below are from `java/samples/semantickernel-concepts/semantickernel-syntax-examples`.

## How to Define an AI Service?

```java {"id":"01J6KPXJRQT6T5CEH6KVKNRXJK"}
ChatCompletionService chatCompletionService = ChatCompletionService.builder()
    .withOpenAIAsyncClient(client)
    .withModelId("gpt-3.5-turbo-0613")
    .withServiceId("fridayChatGeneration")
    .build();
```

## How to Use an AI Service?

- Retrieve the AI Service from the Kernel

```java {"id":"01J6KPXJRQT6T5CEH6KVS31E2W"}
ChatCompletionService service = kernel.getService(ChatCompletionService.class);
```

- Directly call `service.getChatMessageContentsAsync` to get the LLM response

```java {"id":"01J6KPXJRQT6T5CEH6KWNAB38W"}
ChatCompletionService service = kernel.getService(ChatCompletionService.class);
var chatHistory = new ChatHistory(systemMessage);
chatHistory.addUserMessage(userMessage);
var answer = service.getChatMessageContentsAsync(chatHistory, kernel, null).block();
```

## How to Define a KernelBuilder?

The `KernelBuilder` is a builder used to create and configure a new `Kernel` with necessary services and plugins.

```java {"id":"01J6KPXJRQT6T5CEH6M09ZH482"}
ChatCompletionService chatCompletionService = ChatCompletionService.builder()
    .withOpenAIAsyncClient(client)
    .withModelId("gpt-3.5-turbo-0613")
    .withServiceId("fridayChatGeneration")
    .build();

return Kernel.builder()
    .withAIService(ChatCompletionService.class, chatCompletionService);
```

## How to Define a Kernel?

A `Kernel` is created using the `KernelBuilder`, where various services and plugins are configured via `withXXX()`.

Create a Kernel using `KernelBuilder` and configure the necessary parameters

```java {"id":"01J6KPXJRQT6T5CEH6M0KDNH29"}
Kernel kernel = Kernel.builder()
    .withPlugin(myPlugin)
    .withAIService(openAiChatService)
    .withServiceSelector()
    .build();
```

## How to Define a KernelPlugin?

1. Define a custom class
2. Construct using `KernelPluginFactory`

```java {"id":"01J6KPXJRQT6T5CEH6M364H5NF"}
public static class Time {

    @DefineKernelFunction(name = "date")
    public String date() {
        System.out.println("date is called");
        Date now = new Date();
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd");
        return dateFormat.format(now);
    }

    @DefineKernelFunction(name = "time")
    public String time() {
        System.out.println("time is called");
        Date now = new Date();
        SimpleDateFormat timeFormat = new SimpleDateFormat("HH:mm:ss");
        return timeFormat.format(now);
    }
}

KernelPlugin time = KernelPluginFactory.createFromObject(new Time(), "time");
```

## How to Define a KernelFunction?

### Native function

A native function in Semantic Kernel performs precise tasks like data retrieval, time checks, and complex math, which large language models (LLMs) may make mistake. Native functions are written in code and ensure accuracy. In contrast, LLMs offer flexibility, generality, and creativity, excelling in generating and predicting text. Combining both leverages their respective strengths for optimal performance.
For more details, refer to [Microsoft Documentation on Kernel Functions.](https://learn.microsoft.com/en-us/semantic-kernel/agents/plugins/using-the-kernelfunction-decorator?tabs=Csharp)

Here’s an example of how to define a native kernel function:

```java {"id":"01J6KPXJRQT6T5CEH6M40ZZFX9"}
public class TextPlugin {
    @DefineKernelFunction(description = "Change all string chars to uppercase.", name = "Uppercase")
    public String uppercase(@KernelFunctionParameter(description = "Text to uppercase", name = "input") String text) {
        return text.toUpperCase(Locale.ROOT);
    }
}
```

### Inline function

To create a inline KernelFunction from a prompt, you can use either of the following methods, which are equivalent:

- `KernelFunctionFromPrompt.builder().withTemplate(promptTemplate).build();`
- `KernelFunction.createFromPrompt(message).build();`

#### `KernelFunctionFromPrompt.builder().withTemplate(promptTemplate).build();`

```java {"id":"01J6KPXJRQT6T5CEH6M5X7BST8"}
String promptTemplate = """
    Generate a creative reason or excuse for the given event.
    Be creative and be funny. Let your imagination run wild.

    Event: I am running late.
    Excuse: I was being held ransom by giraffe gangsters.

    Event: I haven't been to the gym for a year
    Excuse: I've been too busy training my pet dragon.

    Event: {{$input}}
""".stripIndent();

var excuseFunction = KernelFunctionFromPrompt.builder()
    .withTemplate(promptTemplate)
    .withDefaultExecutionSettings(
        PromptExecutionSettings.builder()
            .withTemperature(0.4)
            .withTopP(1)
            .withMaxTokens(500)
            .withUser("bx-h")
            .build()
    )
    .withName("ExcuseGeneratorFunction")
    .build();
```

#### `KernelFunction.createFromPrompt(message).build();`

```java {"id":"01J6KPXJRQT6T5CEH6M8E78KE4"}
var message = "Translate this date " + date + " to French format";
var fixedFunction = KernelFunction
        .createFromPrompt(message)
        .withDefaultExecutionSettings(
                PromptExecutionSettings.builder()
                        .withMaxTokens(100)
                        .build())
        .withTemplateFormat(PromptTemplateConfig.SEMANTIC_KERNEL_TEMPLATE_FORMAT)
        .withName("translator")
        .build();
```

The `SEMANTIC_KERNEL_TEMPLATE_FORMAT` corresponds to the '__semantic-kernel__' rendering engine, which uses the syntax `{{$variable}}` for variables.

Another rendering engine is **'handlebars'**, which uses the syntax `{{variable}}`.
Here's an example of how to use both:

```java {"id":"01J6KPXJRQT6T5CEH6MBWPS5Q0"}
 runPrompt(kernel,
         "semantic-kernel",
         "Hello AI, my name is {{$name}}. What is the origin of my name?",
         templateFactory);

 runPrompt(kernel,
         "handlebars",
         "Hello AI, my name is {{name}}. What is the origin of my name?",
         templateFactory);
```

The `runPrompt` method is defined as follows:

```java {"id":"01J6KPXJRQT6T5CEH6MEEMMZZZ"}
 public static void runPrompt(Kernel kernel, String templateFormat, String prompt,
                              PromptTemplateFactory templateFactory) {
     var function = new KernelFunctionFromPrompt.Builder<>()
             .withTemplate(prompt)
             .withTemplateFormat(templateFormat)
             .withPromptTemplateFactory(templateFactory)
             .build();

     var arguments = KernelFunctionArguments.builder()
             .withVariable("name", "Bob")
             .build();

     var result = kernel.invokeAsync(function).withArguments(arguments).block();
     System.out.println(result.getResult());
 }
```

For more information, please refer to the following resources:

- [Microsoft Documentation on Prompt Template Syntax](https://learn.microsoft.com/en-us/semantic-kernel/prompts/prompt-template-syntax)
- [Microsoft Devblogs on Using Handlebars Planner in Semantic Kernel](https://devblogs.microsoft.com/semantic-kernel/using-handlebars-planner-in-semantic-kernel/)

### Configuration file

Define a function from a configuration file (json)

```java {"id":"01J6KPXJRQT6T5CEH6MF7SWF40"}
var prompt = "Hello AI, what can you do for me?";
String configPayload = """
      {
      "schema": 1,
      "name": "HelloAI",
      "description": "Say hello to an AI",
      "type": "completion",
      "completion": {
        "max_tokens": 256,
        "temperature": 0.5,
        "top_p": 0.0,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0
      }
    }
""".stripIndent();

PromptTemplateConfig promptConfig = PromptTemplateConfig
    .parseFromJson(configPayload)
    .copy()
    .withTemplate(prompt)
    .build();

var func = KernelFunction
    .createFromPrompt(promptConfig)
    .build();
```

## How to Define a KernelFunctionArguments?

```java {"id":"01J6KPXJRQT6T5CEH6MHNPY67A"}
KernelFunctionArguments.builder().withVariable("input", "Jupiter").build();
```

This can also be done as:

```java {"id":"01J6KPXJRQT6T5CEH6MHV939QS"}
KernelFunctionArguments.builder().withInput("Jupiter").build();
```

## How to Call a KernelFunction?

- Direct call：

```java {"id":"01J6KPXJRQT6T5CEH6MJQM65EB"}
TextPlugin text = new TextPlugin();
return text.uppercase("ciao!");
```

- Invoke via `Kernel.invokeAsync(KernelFunction)`

```java {"id":"01J6KPXJRQT6T5CEH6MN80ST21"}
Kernel kernel = Kernel.builder().build();
KernelPlugin kernelPlugin = KernelPluginFactory.createFromObject(new StaticTextPlugin(), "text");
KernelFunctionArguments arguments = KernelFunctionArguments.builder()
    .withVariable("input", "Today is: ")
    .withVariable("day", "Monday")
    .build();

return kernel.invokeAsync(kernelPlugin.get("AppendDay"))
    .withArguments(arguments)
    .block()
    .getResult();
```

OR:

```java {"id":"01J6KPXJRQT6T5CEH6MNJMH977"}
var result = kernel
    .invokeAsync(excuseFunction)
    .withArguments(
        KernelFunctionArguments.builder()
            .withInput("I missed the F1 final race")
            .build()
    )
    .block();
```

## How to Define a PromptTemplate?

The purpose of a prompt template is to:

- Render the prompt
- Be passed as a parameter to `createFromPrompt()` to construct `KernelFunction`

### Using `KernelPromptTemplateFactory.tryCreate(PromptTemplateConfig)`

1. Define the prompt template
2. Create using `KernelPromptTemplateFactory()`

```java {"id":"01J6KPXJRQT6T5CEH6MNRY38ZB"}
String functionDefinition = """
    Today is: {{time.date}}
    Current time is: {{time.time}}

    Answer the following questions using JSON syntax, including the data used.
    Is it morning, afternoon, evening, or night (morning/afternoon/evening/night)?
    Is it weekend time (weekend/not weekend)?
""";

PromptTemplate promptTemplate = new KernelPromptTemplateFactory().tryCreate(
    PromptTemplateConfig
        .builder()
        .withTemplate(functionDefinition)
        .build()
);
```

### Create using `PromptTemplateFactory.build`

```java {"id":"01J6KPXJRQT6T5CEH6MSA6S03R"}
String systemPromptTemplate = "...";
PromptTemplate promptTemplate = PromptTemplateFactory.build(
    PromptTemplateConfig
        .builder()
        .withTemplate(systemPromptTemplate)
        .build()
);
```

## How to Render a Prompt Without Sending an LLM Query?

```java {"id":"01J6KPXJRQT6T5CEH6MTF92YA0"}
var renderedPrompt = promptTemplate.renderAsync(kernel, KernelFunctionArguments, InvocationContext).block();
System.out.println(renderedPrompt);
```

## Hooks

Hooks are functions triggered in specific situations attached to the kernel.

- **Global Registration**: If added to `kernel.getGlobalKernelHooks()`, it is globally effective

```java {"id":"01J6KPXJRQT6T5CEH6MYCK9W2P"}
kernel.getGlobalKernelHooks().addHook("hookName", KernelHook);
```

- **Single Call Registration**: If passed as a parameter in `invokeAsync`, it is effective for that call only

```java {"id":"01J6KPXJRQT6T5CEH6MZ97AFDS"}
KernelHooks kernelHooks = new KernelHooks();
kernelHooks.addPreChatCompletionHook(...);

var result = kernel.invokeAsync(writerFunction)
    .withArguments(KernelFunctionArguments.builder().build())
    .addKernelHooks(kernelHooks)
    .block();
```

### FunctionInvokingHook

Triggered before function call.

```java {"id":"01J6KPXJRQT6T5CEH6N27PW4KE"}
FunctionInvokingHook preHook = event -> {
    System.out.println(event.getFunction().getName() + " : Pre Execution Handler - Triggered");
    return event;
};
kernel.getGlobalKernelHooks().addHook("", preHook);
```

### FunctionInvokedHook

Triggered after function call

```java {"id":"01J6KPXJRQT6T5CEH6N5720DFQ"}
FunctionInvokedHook hook = event -> {
    String result = (String) event.getResult().getResult();
    System.out.println(event.getFunction().getName() + " : Modified result via FunctionInvokedHook: " + result);
    result = result.replaceAll("[aeiouAEIOU0-9]", "*");

    return new FunctionInvokedEvent(
        event.getFunction(),
        event.getArguments(),
        new FunctionResult<>(ContextVariable.of(result), event.getResult().getMetadata(), result)
    );
};
kernel.getGlobalKernelHooks().addHook(hook);
```

### PromptRenderingHook

```java {"id":"01J6KPXJRQT6T5CEH6N73XFXFW"}
PromptRenderingHook myRenderingHandler = event -> {
    System.out.println(event.getFunction().getName() + " : Triggered PromptRenderingHook");
    event.getArguments().put("style", ContextVariable.of("Seinfeld"));
    return event;
};
```

### PromptRenderedHook

```java {"id":"01J6KPXJRQT6T5CEH6N8X4EW42"}
PromptRenderedHook myRenderedHandler = event -> {
    System.out.println(event.getFunction().getName() + " : Triggered PromptRenderedHook");
    String prompt = event.getPrompt() + "\nUSE SHORT, CLEAR, COMPLETE SENTENCES.";
    return new PromptRenderedEvent(event.getFunction(), event.getArguments(), prompt);
};
```

> `PromptRenderingHook` and `PromptRenderedHook` are triggered only at the start of a conversation. They won't trigger during multiple tool calls. To trigger at every LLM interaction, use `ChatCompletionsHook`

### PreChatCompletionHook

Add a pre-chat completion hook to add instructions before ChatCompletion.

```java {"id":"01J6KPXJRQT6T5CEH6NCA43CJD"}
kernel.getGlobalKernelHooks().addPreChatCompletionHook(event -> {
    ChatCompletionsOptions options = event.getOptions();
    List<ChatRequestMessage> messages = options.getMessages();
    messages = new ArrayList<>(messages);
    messages.add(new ChatRequestSystemMessage("Use upper case text when responding to the prompt."));
    System.out.println("------- Triggered before ChatCompletion -------");
    System.out.println("---- Added: Use upper case text when responding to the prompt. ----");
    for (ChatRequestMessage msg : messages) {
        System.out.println(msg);
    }

    return new PreChatCompletionEvent(
        PreChatCompletionHook.cloneOptionsWithMessages(options, messages)
    );
});
```

### PostChatCompletionHook

Add a post-chat completion hook to adjust the output format

```java {"id":"01J6KPXJRQT6T5CEH6NF78EEA5"}
kernel.getGlobalKernelHooks().addPostChatCompletionHook(event -> {
    System.out.println("------- Triggered after ChatCompletion -------");
    System.out.println("--- Output ChatCompletion and id ----");
    System.out.println("Chat completion");
    System.out.println("Id: " + event.getChatCompletions().getId());
    return event;
});
```
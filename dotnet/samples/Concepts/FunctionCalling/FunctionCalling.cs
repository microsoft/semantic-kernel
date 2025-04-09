// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace FunctionCalling;

/// <summary>
/// These examples demonstrate how to enable and configure various aspects of function calling model in SK using the different function choice behaviors:
/// <see cref="FunctionChoiceBehavior.Auto"/>, <see cref="FunctionChoiceBehavior.Required"/>, and <see cref="FunctionChoiceBehavior.None"/>.
/// The behaviors define the following aspect of function calling model:
/// 1. Function advertising - the list of functions to provide to the AI model. All three can advertise all kernel functions or a specified subset of them.
/// 2. Function calling behavior - whether the AI model automatically selects functions to call, is forced to call provided functions, or has to describe which functions it would call without calling them to complete the prompt.
/// 3. Function invocation - whether functions are invoked automatically by SK or manually by a caller and whether they are invoked sequentially or concurrently(not supported in auto-invocation mode yet)
///
/// ** Function advertising **
///    All three behaviors have the `functions` parameter of type <see cref="IEnumerable{KernelFunction}"/>. By default, it is null,
///    which means all kernel functions are provided or advertised to the AI model. If a list of functions is provided,
///    only those functions are advertised to the AI model. An empty list means no functions are provided to the AI model,
///    which is equivalent to disabling function calling.
///
/// ** Function calling behavior **
///    The <see cref="FunctionChoiceBehavior.Auto"/> behavior allows the model to decide whether to call the functions and, if so, which ones to call.
///    The <see cref="FunctionChoiceBehavior.Required"/> behavior forces the model to call the provided functions. The behavior advertises functions in the first
///    request to the AI model only and stops advertising them in subsequent requests to prevent an infinite loop where the model keeps calling functions repeatedly.
///    The <see cref="FunctionChoiceBehavior.None"/> behavior tells the AI model to use the provided functions without calling them to generate a response.
///    This behavior is useful for dry runs when you want to see which functions the model would call without actually invoking them.
///
/// ** Function invocation **
///    The <see cref="FunctionChoiceBehavior.Auto"/> and <see cref="FunctionChoiceBehavior.Required"/> supports two modes of function invocation: manual and automatic:
///    * Automatic function invocation mode causes all functions chosen by the AI model to be automatically invoked by SK.
///      The results of these function invocations are added to the chat history and sent to the model automatically in the following request.
///      The model then reasons about the chat history and then calls functions again or generates the final response.
///      This approach is fully automated and requires no manual intervention from the caller. The automatic invocation mode is enabled by default.
///    * Manual invocation mode returns all function calls requested by the AI model to the SK caller. The caller is fully responsible
///      for the invocation phase where they may decide which function to call, how to handle exceptions, call them in parallel or sequentially, etc.
///      The caller then adds the function results/exceptions to the chat history and returns it to the model, which reasons about it
///      and then calls functions again or generates the final response. This invocation mode provides more control over the function invocation phase to the caller.
///      To enable manual invocation, the caller needs to set the `autoInvoke` parameter to `false` when specifying either <see cref="FunctionChoiceBehavior.Auto"/>
///      or <see cref="FunctionChoiceBehavior.Required"/> in the <see cref="PromptExecutionSettings"/>.
///
/// ** Options **
///    The following aspects of the function choice behaviors can be changed via the `options` constructor's parameter of type <see cref="FunctionChoiceBehaviorOptions"/> each behavior accepts:
///    * The <see cref="FunctionChoiceBehaviorOptions.AllowConcurrentInvocation"/> option enables concurrent invocation of functions by SK.
///      By default, this option is set to false, meaning that functions are invoked sequentially. Concurrent invocation is only possible if the AI model can
///      call or select multiple functions for invocation in a single request; otherwise, there is no distinction between sequential and concurrent invocation.
///    * The <see cref="FunctionChoiceBehaviorOptions.AllowParallelCalls"/> option instructs the AI model to call multiple functions in one request if the model supports parallel function calls.
///      By default, this option is set to null, meaning that the AI model default value will be used.
///
///    The following table summarizes the effects of various combinations of the AllowParallelCalls and AllowConcurrentInvocation options:
///
///    | AllowParallelCalls  | AllowConcurrentInvocation | # of functions chosen per AI roundtrip  | Concurrent Invocation by SK |
///    |---------------------|---------------------------|-----------------------------------------|-----------------------------|
///    | false               | false                     | one                                     | false                       |
///    | false               | true                      | one                                     | false*                      |
///    | true                | false                     | multiple                                | false                       |
///    | true                | true                      | multiple                                | true                        |
///
///    `*` There's only one function to invoke.
/// </summary>
public class FunctionCalling(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This example demonstrates usage of <see cref="FunctionChoiceBehavior.Auto"/> that advertises all kernel functions to the AI model and invokes them automatically.
    /// </summary>
    [Fact]
    public async Task RunPromptWithAutoFunctionChoiceBehaviorAdvertisingAllKernelFunctionsInvokedAutomaticallyAsync()
    {
        Kernel kernel = CreateKernel();

        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        Console.WriteLine(await kernel.InvokePromptAsync("What is the likely color of the sky in Boston today?", new(settings)));

        // Expected output: "Boston is currently experiencing a rainy day, hence, the likely color of the sky in Boston is grey."
    }

    /// <summary>
    /// This example demonstrates usage of <see cref="FunctionChoiceBehavior.Required"/> that advertises only one function to the AI model and invokes it automatically.
    /// </summary>
    [Fact]
    public async Task RunPromptWithRequiredFunctionChoiceBehaviorAdvertisingOneFunctionInvokedAutomaticallyAsync()
    {
        Kernel kernel = CreateKernel();

        KernelFunction getWeatherFunction = kernel.Plugins.GetFunction("HelperFunctions", "GetWeatherForCity");

        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Required(functions: [getWeatherFunction]) };

        Console.WriteLine(await kernel.InvokePromptAsync("Given that it is now the 9th of September 2024, 11:29 AM, what is the likely color of the sky in Boston?", new(settings)));

        // Expected output: "The sky in Boston is likely to be grey due to the rain."
    }

    /// <summary>
    /// This example demonstrates usage of <see cref="FunctionChoiceBehavior.None"/> that advertises all kernel functions to the AI model.
    /// </summary>
    [Fact]
    public async Task RunPromptWithNoneFunctionChoiceBehaviorAdvertisingAllKernelFunctionsAsync()
    {
        Kernel kernel = CreateKernel();

        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.None() };

        Console.WriteLine(await kernel.InvokePromptAsync("Tell me which provided functions I would need to call to get the color of the sky in Boston for today.", new(settings)));

        // Expected output: "You would first call the `HelperFunctions-GetCurrentUtcDateTime` function to get the current date time in UTC. Then, you would use the `HelperFunctions-GetWeatherForCity` function,
        //                   passing in the city name as 'Boston' and the retrieved UTC date time. Note, however, that these functions won't directly tell you the color of the sky.
        //                   The `GetWeatherForCity` function would provide weather data, and you may infer the general sky condition (e.g., clear, cloudy, rainy) based on this data, but it would not specify the color of the sky."
    }

    /// <summary>
    /// This example demonstrates usage of <see cref="FunctionChoiceBehavior.Auto"/> in YAML prompt template config that advertises all kernel functions to the AI model and invokes them automatically.
    /// </summary>
    [Fact]
    public async Task RunPromptTemplateConfigWithAutoFunctionChoiceBehaviorAdvertisingAllKernelFunctionsInvokedAutomaticallyAsync()
    {
        Kernel kernel = CreateKernel();

        // The `function_choice_behavior.functions` property is omitted which is equivalent to providing all kernel functions to the AI model.
        string promptTemplateConfig = """
            template_format: semantic-kernel
            template: What is the likely color of the sky in Boston today?
            execution_settings:
              default:
                function_choice_behavior:
                  type: auto
            """;

        KernelFunction promptFunction = KernelFunctionYaml.FromPromptYaml(promptTemplateConfig);

        Console.WriteLine(await kernel.InvokeAsync(promptFunction));

        // Expected output: "Given that it's currently raining in Boston, the sky is likely to be gray."
    }

    /// <summary>
    /// This example demonstrates usage of <see cref="FunctionChoiceBehavior.Auto"/> in YAML prompt template config that advertises one kernel function to the AI model and invokes it automatically.
    /// </summary>
    [Fact]
    public async Task RunPromptTemplateConfigWithAutoFunctionChoiceBehaviorAdvertisingOneFunctionInvokedAutomaticallyAsync()
    {
        Kernel kernel = CreateKernel();

        // Only the `HelperFunctions.GetWeatherForCity` function which is added to the `function_choice_behavior.functions` list, is advertised to the AI model.
        string promptTemplateConfig = """
            template_format: semantic-kernel
            template: Given that it is now the 9th of September 2024, 11:29 AM, what is the likely color of the sky in Boston?
            execution_settings:
              default:
                function_choice_behavior:
                  type: auto
                  functions:
                    - HelperFunctions.GetWeatherForCity
            """;

        KernelFunction promptFunction = KernelFunctionYaml.FromPromptYaml(promptTemplateConfig);

        Console.WriteLine(await kernel.InvokeAsync(promptFunction));

        // Expected output: "The color of the sky in Boston is likely to be grey due to the rain."
    }

    [Fact]
    /// <summary>
    /// This example demonstrates usage of the non-streaming chat completion API with <see cref="FunctionChoiceBehavior.Auto"/> that advertises all kernel functions to the AI model and invokes them automatically.
    /// </summary>
    public async Task RunNonStreamingChatCompletionApiWithAutomaticFunctionInvocationAsync()
    {
        Kernel kernel = CreateKernel();

        // To enable automatic function invocation, set the `autoInvoke` parameter to `true` in the line below or omit it as it is `true` by default.
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        ChatMessageContent result = await chatCompletionService.GetChatMessageContentAsync(
            "What is the likely color of the sky in Boston today?",
            settings,
            kernel);

        // Assert
        Console.WriteLine(result);

        // Expected output: "The likely color of the sky in Boston is gray due to the current rainy weather."
    }

    [Fact]
    /// <summary>
    /// This example demonstrates the usage of the streaming chat completion API with <see cref="FunctionChoiceBehavior.Auto"/> that advertises all kernel functions to the AI model and invokes them automatically.
    /// </summary>
    public async Task RunStreamingChatCompletionApiWithAutomaticFunctionInvocationAsync()
    {
        Kernel kernel = CreateKernel();

        // To enable automatic function invocation, set the `autoInvoke` parameter to `true` in the line below or omit it as it is `true` by default.
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        var stringBuilder = new StringBuilder();

        // Act
        await foreach (var update in chatCompletionService.GetStreamingChatMessageContentsAsync(
            "What is the likely color of the sky in Boston today?",
            settings,
            kernel))
        {
            stringBuilder.Append(update.Content);
        }

        // Assert
        Console.WriteLine(stringBuilder.ToString());

        // Expected output: "Given that it's currently daytime and rainy in Boston, the sky is likely to be grey or overcast."
    }

    /// <summary>
    /// This example demonstrates the usage of the non-streaming chat completion API with <see cref="FunctionChoiceBehavior.Auto"/> that advertises all kernel functions to the AI model and invokes them manually.
    /// </summary>
    [Fact]
    public async Task RunNonStreamingChatCompletionApiWithManualFunctionInvocationAsync()
    {
        Kernel kernel = CreateKernel();

        IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // To enable manual function invocation, set the `autoInvoke` parameter to `false`.
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = Microsoft.SemanticKernel.FunctionChoiceBehavior.Auto(autoInvoke: false) };

        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("What is the likely color of the sky in Boston today?");

        while (true)
        {
            // Start or continue chat based on the chat history
            ChatMessageContent result = await chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, kernel);
            if (result.Content is not null)
            {
                Console.Write(result.Content);
                // Expected output: "The color of the sky in Boston is likely to be gray due to the rainy weather."
            }

            // Get function calls from the chat message content and quit the chat loop if no function calls are found.
            IEnumerable<FunctionCallContent> functionCalls = FunctionCallContent.GetFunctionCalls(result);
            if (!functionCalls.Any())
            {
                break;
            }

            // Preserving the original chat message content with function calls in the chat history.
            chatHistory.Add(result);

            // Iterating over the requested function calls and invoking them sequentially.
            // The code can easily be modified to invoke functions in concurrently if needed.
            foreach (FunctionCallContent functionCall in functionCalls)
            {
                try
                {
                    // Invoking the function
                    FunctionResultContent resultContent = await functionCall.InvokeAsync(kernel);

                    // Adding the function result to the chat history
                    chatHistory.Add(resultContent.ToChatMessage());
                }
                catch (Exception ex)
                {
                    // Adding function exception to the chat history.
                    chatHistory.Add(new FunctionResultContent(functionCall, ex).ToChatMessage());
                    // or
                    //chatHistory.Add(new FunctionResultContent(functionCall, "Error details that the AI model can reason about.").ToChatMessage());
                }
            }

            Console.WriteLine();
        }
    }

    /// <summary>
    /// This example demonstrates the usage of the streaming chat completion API with <see cref="FunctionChoiceBehavior.Auto"/> that advertises all kernel functions to the AI model and invokes them manually.
    /// </summary>
    [Fact]
    public async Task RunStreamingChatCompletionApiWithManualFunctionCallingAsync()
    {
        Kernel kernel = CreateKernel();

        IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // To enable manual function invocation, set the `autoInvoke` parameter to `false`.
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = Microsoft.SemanticKernel.FunctionChoiceBehavior.Auto(autoInvoke: false) };

        // Create chat history with the initial user message
        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("What is the likely color of the sky in Boston today?");

        while (true)
        {
            AuthorRole? authorRole = null;
            var fccBuilder = new FunctionCallContentBuilder();

            // Start or continue streaming chat based on the chat history
            await foreach (var streamingContent in chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory, settings, kernel))
            {
                if (streamingContent.Content is not null)
                {
                    Console.Write(streamingContent.Content);
                    // Streamed output: "The color of the sky in Boston is likely to be gray due to the rainy weather."
                }
                authorRole ??= streamingContent.Role;
                fccBuilder.Append(streamingContent);
            }

            // Build the function calls from the streaming content and quit the chat loop if no function calls are found
            var functionCalls = fccBuilder.Build();
            if (!functionCalls.Any())
            {
                break;
            }

            // Creating and adding chat message content to preserve the original function calls in the chat history.
            // The function calls are added to the chat message a few lines below.
            var fcContent = new ChatMessageContent(role: authorRole ?? default, content: null);
            chatHistory.Add(fcContent);

            // Iterating over the requested function calls and invoking them.
            // The code can easily be modified to invoke functions in concurrently if needed.
            foreach (var functionCall in functionCalls)
            {
                // Adding the original function call to the chat message content
                fcContent.Items.Add(functionCall);

                // Invoking the function
                var functionResult = await functionCall.InvokeAsync(kernel);

                // Adding the function result to the chat history
                chatHistory.Add(functionResult.ToChatMessage());
            }

            Console.WriteLine();
        }
    }

    /// <summary>
    /// This example demonstrates how a simulated function can be added to the chat history a manual function mode.
    /// </summary>
    /// <remarks>
    /// Simulated functions are not called or requested by the AI model but are added to the chat history by the caller.
    /// They provide a way for callers to add additional information that, if provided via the prompt, would be ignored due to the model training.
    /// </remarks>
    [Fact]
    public async Task RunNonStreamingPromptWithSimulatedFunctionAsync()
    {
        Kernel kernel = CreateKernel();

        IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Enabling manual function invocation
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = Microsoft.SemanticKernel.FunctionChoiceBehavior.Auto(autoInvoke: false) };

        ChatHistory chatHistory = [];
        chatHistory.AddUserMessage("What is the likely color of the sky in Boston today?");

        while (true)
        {
            ChatMessageContent result = await chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, kernel);
            if (result.Content is not null)
            {
                Console.Write(result.Content);
                // Expected output: "Considering the current weather conditions in Boston with a tornado watch in effect resulting in potential severe thunderstorms,
                // the sky color is likely unusual such as green, yellow, or dark gray. Please stay safe and follow instructions from local authorities."
            }

            chatHistory.Add(result); // Adding AI model response containing function calls(requests) to chat history as it's required by the models.

            IEnumerable<FunctionCallContent> functionCalls = FunctionCallContent.GetFunctionCalls(result);
            if (!functionCalls.Any())
            {
                break;
            }

            foreach (FunctionCallContent functionCall in functionCalls)
            {
                FunctionResultContent resultContent = await functionCall.InvokeAsync(kernel); // Invoking each function.

                chatHistory.Add(resultContent.ToChatMessage());
            }

            // Adding a simulated function call to the connector response message
            FunctionCallContent simulatedFunctionCall = new("weather-alert", id: "call_123");
            result.Items.Add(simulatedFunctionCall);

            // Adding a simulated function result to chat history
            string simulatedFunctionResult = "A Tornado Watch has been issued, with potential for severe thunderstorms causing unusual sky colors like green, yellow, or dark gray. Stay informed and follow safety instructions from authorities.";
            chatHistory.Add(new FunctionResultContent(simulatedFunctionCall, simulatedFunctionResult).ToChatMessage());

            Console.WriteLine();
        }
    }

    /// <summary>
    /// This example demonstrates how to disable function calling.
    /// </summary>
    [Fact]
    public async Task DisableFunctionCallingAsync()
    {
        Kernel kernel = CreateKernel();

        // Supplying an empty list to the `functions` parameter disables function calling.
        // Alternatively, either omit assigning anything to the `FunctionChoiceBehavior` property or assign null to it to also disable function calling.  
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(functions: []) };

        Console.WriteLine(await kernel.InvokePromptAsync("What is the likely color of the sky in Boston today?", new(settings)));

        // Expected output: "Sorry, I cannot answer this question as it requires real-time information which I, as a text-based model, cannot access."
    }

    /// <summary>
    /// This example demonstrates how to disable function calling in the YAML prompt template config.
    /// </summary>
    [Fact]
    public async Task DisableFunctionCallingInPromptTemplateConfigAsync()
    {
        Kernel kernel = CreateKernel();

        // The `function_choice_behavior.functions` property is an empty list which disables function calling.
        // Alternatively, you can omit the `function_choice_behavior` property to disable function calling.
        string promptTemplateConfig = """
            template_format: semantic-kernel
            template: Given that it is now the 9th of September 2024, 11:29 AM, what is the likely color of the sky in Boston?
            execution_settings:
              default:
                function_choice_behavior:
                  type: auto
                  functions: []
            """;

        KernelFunction promptFunction = KernelFunctionYaml.FromPromptYaml(promptTemplateConfig);

        Console.WriteLine(await kernel.InvokeAsync(promptFunction));

        // Expected output: "As an AI, I don't have real-time data or live feed to provide current weather conditions or the color of the sky."
    }

    [Fact]
    /// <summary>
    /// This example demonstrates usage of the non-streaming chat completion API with <see cref="FunctionChoiceBehavior.Auto"/> that advertises all kernel functions to the AI model and invokes them automatically in concurrent manner.
    /// </summary>
    public async Task RunNonStreamingChatCompletionApiWithConcurrentFunctionInvocationOptionAsync()
    {
        Kernel kernel = CreateKernel();

        // The `AllowConcurrentInvocation` option enables concurrent invocation of functions.
        FunctionChoiceBehaviorOptions options = new() { AllowConcurrentInvocation = true };

        // To enable automatic function invocation, set the `autoInvoke` parameter to `true` in the line below or omit it as it is `true` by default.
        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: options) };

        IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        ChatMessageContent result = await chatCompletionService.GetChatMessageContentAsync(
            "Good morning! What’s the current time and latest news headlines?",
            settings,
            kernel);

        // Assert
        Console.WriteLine(result);

        // Expected output: Good morning! The current UTC time is 07:47 on October 22, 2024. Here are the latest news headlines: 1. Squirrel Steals Show - Discover the unexpected star of a recent event. 2. Dog Wins Lottery - Unbelievably, a lucky canine has hit the jackpot.
    }

    [Fact]
    /// <summary>
    /// This example demonstrates usage of the non-streaming chat completion API with <see cref="FunctionChoiceBehavior.Auto"/> that
    /// advertises all kernel functions to the AI model and instructs the model to call multiple functions in parallel.
    /// </summary>
    public async Task RunNonStreamingChatCompletionApiWithParallelFunctionCallOptionAsync()
    {
        Kernel kernel = CreateKernel();

        // The `AllowParallelCalls` option instructs the AI model to call multiple functions in parallel if the model supports parallel function calls.
        FunctionChoiceBehaviorOptions options = new() { AllowParallelCalls = true };

        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: options) };

        IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        ChatMessageContent result = await chatCompletionService.GetChatMessageContentAsync(
            "Good morning! What’s the current time and latest news headlines?",
            settings,
            kernel);

        // Assert
        Console.WriteLine(result);

        // Expected output: Good morning! The current UTC time is 07:47 on October 22, 2024. Here are the latest news headlines: 1. Squirrel Steals Show - Discover the unexpected star of a recent event. 2. Dog Wins Lottery - Unbelievably, a lucky canine has hit the jackpot.
    }

    [Fact]
    /// <summary>
    /// This example demonstrates usage of the non-streaming chat completion API with <see cref="FunctionChoiceBehavior.Auto"/> that
    /// advertises all kernel functions to the AI model, instructs the model to call multiple functions in parallel, and invokes them concurrently.
    /// </summary>
    public async Task RunNonStreamingChatCompletionApiWithParallelFunctionCallAndConcurrentFunctionInvocationOptionsAsync()
    {
        Kernel kernel = CreateKernel();

        // The `AllowParallelCalls` option instructs the AI model to call multiple functions in parallel if the model supports parallel function calls.
        // The `AllowConcurrentInvocation` option enables concurrent invocation of the functions.
        FunctionChoiceBehaviorOptions options = new() { AllowParallelCalls = true, AllowConcurrentInvocation = true };

        OpenAIPromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: options) };

        IChatCompletionService chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        ChatMessageContent result = await chatCompletionService.GetChatMessageContentAsync(
            "Good morning! What’s the current time and latest news headlines?",
            settings,
            kernel);

        // Assert
        Console.WriteLine(result);

        // Expected output: Good morning! The current UTC time is 07:47 on October 22, 2024. Here are the latest news headlines: 1. Squirrel Steals Show - Discover the unexpected star of a recent event. 2. Dog Wins Lottery - Unbelievably, a lucky canine has hit the jackpot.
    }

    /// <summary>
    /// Creates a kernel with the OpenAI chat completion model and some helper functions.
    /// </summary>
    /// <param name="output">Optionally set this to log the function calling requests and responses</param>
    private static Kernel CreateKernel(ITestOutputHelper? output = null)
    {
        // Create kernel
        IKernelBuilder builder = Kernel.CreateBuilder();

        // Create a logging handler to output HTTP requests and responses
        if (output is not null)
        {
            builder.AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey);
        }
        else
        {
            builder.AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey);
        }

        Kernel kernel = builder.Build();

        // Add a plugin with some helper functions we want to allow the model to call.
        kernel.ImportPluginFromFunctions("HelperFunctions",
        [
            kernel.CreateFunctionFromMethod(() => new List<string> { "Squirrel Steals Show", "Dog Wins Lottery" }, "GetLatestNewsTitles", "Retrieves latest news titles."),
            kernel.CreateFunctionFromMethod(() => DateTime.UtcNow.ToString("R"), "GetCurrentDateTimeInUtc", "Retrieves the current date time in UTC."),
            kernel.CreateFunctionFromMethod((string cityName, string currentDateTimeInUtc) =>
                cityName switch
                {
                    "Boston" => "61 and rainy",
                    "London" => "55 and cloudy",
                    "Miami" => "80 and sunny",
                    "Paris" => "60 and rainy",
                    "Tokyo" => "50 and sunny",
                    "Sydney" => "75 and sunny",
                    "Tel Aviv" => "80 and sunny",
                    _ => "31 and snowing",
                }, "GetWeatherForCity", "Gets the current weather for the specified city and specified date time."),
        ]);

        return kernel;
    }
}

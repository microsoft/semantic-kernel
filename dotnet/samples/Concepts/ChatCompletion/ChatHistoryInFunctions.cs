// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace ChatCompletion;

/// <summary>
/// This example shows how to access <see cref="ChatHistory"/> object in Semantic Kernel functions using
/// <see cref="Kernel.Data"/> and <see cref="KernelArguments"/>.
/// This scenario can be useful with auto function calling,
/// when logic in SK functions depends on results from previous messages in the same chat history.
/// </summary>
public sealed class ChatHistoryInFunctions(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This method passes an instance of <see cref="ChatHistory"/> to SK function using <see cref="Kernel.Data"/> property.
    /// This approach should be used with caution for cases when Kernel is registered in application as singleton.
    /// For singleton Kernel, check examples <see cref="UsingKernelArgumentsAndFilterOption1Async"/> and <see cref="UsingKernelArgumentsAndFilterOption2Async"/>.
    /// </summary>
    [Fact]
    public async Task UsingKernelDataAsync()
    {
        // Initialize kernel.
        var kernel = GetKernel();

        // Import plugin.
        kernel.ImportPluginFromObject(new DataPlugin(this.Output));

        // Get chat completion service.
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Initialize chat history with prompt.
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("I want to get an information about featured products, product reviews and daily summary.");

        // Initialize execution settings with enabled auto function calling.
        var executionSettings = new OpenAIPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        // Set chat history in kernel data to access it in a function.
        kernel.Data[nameof(ChatHistory)] = chatHistory;

        // Send a request.
        var result = await chatCompletionService.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

        // Each function will receive a greater number of messages in chat history, because chat history is populated
        // with results of previous functions.
        Console.WriteLine($"Result: {result}");

        // Output:
        // GetFeaturedProducts - Chat History Message Count: 2
        // GetProductReviews - Chat History Message Count: 3
        // GetDailySalesSummary - Chat History Message Count: 4
        // Result: Here's the information you requested...
    }

    /// <summary>
    /// This method passes an instance of <see cref="ChatHistory"/> to SK function using
    /// <see cref="KernelArguments"/> and <see cref="IAutoFunctionInvocationFilter"/> filter.
    /// The plugin has access to <see cref="KernelArguments"/>, so it's possible to find a chat history in arguments by property name.
    /// </summary>
    [Fact]
    public async Task UsingKernelArgumentsAndFilterOption1Async()
    {
        // Initialize kernel.
        var kernel = GetKernel();

        // Import plugin.
        kernel.ImportPluginFromObject(new DataPlugin(this.Output));

        // Add filter.
        kernel.AutoFunctionInvocationFilters.Add(new AutoFunctionInvocationFilter());

        // Initialize execution settings with enabled auto function calling.
        var executionSettings = new OpenAIPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        // Send a request.
        var result = await kernel.InvokePromptAsync("I want to get an information about featured products, product reviews and daily summary.", new(executionSettings));

        // Each function will receive a greater number of messages in chat history, because chat history is populated
        // with results of previous functions.
        Console.WriteLine($"Result: {result}");

        // Output:
        // GetFeaturedProducts - Chat History Message Count: 2
        // GetProductReviews - Chat History Message Count: 3
        // GetDailySalesSummary - Chat History Message Count: 4
        // Result: Here's the information you requested...
    }

    /// <summary>
    /// This method passes an instance of <see cref="ChatHistory"/> to SK function using
    /// <see cref="KernelArguments"/> and <see cref="IAutoFunctionInvocationFilter"/> filter.
    /// The plugin has access to <see cref="ChatHistory"/> directly, since it's automatically injected from <see cref="KernelArguments"/>
    /// into the function by argument name.
    /// </summary>
    [Fact]
    public async Task UsingKernelArgumentsAndFilterOption2Async()
    {
        // Initialize kernel.
        var kernel = GetKernel();

        // Import plugin.
        kernel.ImportPluginFromObject(new EmailPlugin(this.Output));

        // Add filter.
        kernel.AutoFunctionInvocationFilters.Add(new AutoFunctionInvocationFilter());

        // Initialize execution settings with enabled auto function calling.
        var executionSettings = new OpenAIPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        // Send a request.
        var result = await kernel.InvokePromptAsync("Send email to test@contoso.com", new(executionSettings));

        Console.WriteLine($"Result: {result}");

        // Output:
        // SendEmail - Chat History Message Count: 2
        // Result: Email has been sent to test@contoso.com.
    }

    #region private

    /// <summary>
    /// Implementation of <see cref="IAutoFunctionInvocationFilter"/> to set chat history in <see cref="KernelArguments"/>
    /// before invoking a function.
    /// </summary>
    private sealed class AutoFunctionInvocationFilter : IAutoFunctionInvocationFilter
    {
        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            // Set chat history in kernel arguments.
            if (context.Arguments is not null)
            {
                // nameof(ChatHistory) is used for demonstration purposes.
                // Any name can be used here, as long as it is effective for the intended purpose.
                // However, the same name must be used when retrieving chat history from the KernelArguments instance
                // or when the ChatHistory parameter is directly injected into a function.
                context.Arguments[nameof(ChatHistory)] = context.ChatHistory;
            }

            // Invoke next filter in pipeline or function.
            await next(context);
        }
    }

    /// <summary>
    /// Data plugin for demonstration purposes, where methods accept <see cref="Kernel"/> and <see cref="KernelArguments"/>
    /// as parameters.
    /// </summary>
    private sealed class DataPlugin(ITestOutputHelper output)
    {
        [KernelFunction]
        public List<string> GetFeaturedProducts(Kernel kernel, KernelArguments arguments)
        {
            var chatHistory = GetChatHistory(kernel.Data) ?? GetChatHistory(arguments);

            if (chatHistory is not null)
            {
                output.WriteLine($"{nameof(GetFeaturedProducts)} - Chat History Message Count: {chatHistory.Count}");
            }

            return ["Laptop", "Smartphone", "Smartwatch"];
        }

        [KernelFunction]
        public Dictionary<string, List<string>> GetProductReviews(Kernel kernel, KernelArguments arguments)
        {
            var chatHistory = GetChatHistory(kernel.Data) ?? GetChatHistory(arguments);

            if (chatHistory is not null)
            {
                output.WriteLine($"{nameof(GetProductReviews)} - Chat History Message Count: {chatHistory.Count}");
            }

            return new()
            {
                ["Laptop"] = ["Excellent performance!", "Battery life could be better."],
                ["Smartphone"] = ["Amazing camera!", "Very responsive."],
                ["Smartwatch"] = ["Stylish design", "Could use more apps."],
            };
        }

        [KernelFunction]
        public string GetDailySalesSummary(Kernel kernel, KernelArguments arguments)
        {
            var chatHistory = GetChatHistory(kernel.Data) ?? GetChatHistory(arguments);

            if (chatHistory is not null)
            {
                output.WriteLine($"{nameof(GetDailySalesSummary)} - Chat History Message Count: {chatHistory.Count}");
            }

            const int OrdersProcessed = 50;
            const decimal TotalRevenue = 12345.67m;

            return $"Today's Sales: {OrdersProcessed} orders processed, total revenue: ${TotalRevenue}.";
        }

        private static ChatHistory? GetChatHistory(IDictionary<string, object?> data)
        {
            if (data.TryGetValue(nameof(ChatHistory), out object? chatHistoryObj) &&
                chatHistoryObj is ChatHistory chatHistory)
            {
                return chatHistory;
            }

            return null;
        }
    }

    /// <summary>
    /// Email plugin for demonstration purposes, where method accepts <see cref="ChatHistory"/> as parameter.
    /// </summary>
    private sealed class EmailPlugin(ITestOutputHelper output)
    {
        [KernelFunction]
        public string SendEmail(string to, ChatHistory? chatHistory = null)
        {
            if (chatHistory is not null)
            {
                output.WriteLine($"{nameof(SendEmail)} - Chat History Message Count: {chatHistory.Count}");
            }

            // Simulate the email-sending process by notifying the AI model that the email was sent.
            return $"Email has been sent to {to}";
        }
    }

    /// <summary>
    /// Helper method to initialize <see cref="Kernel"/>.
    /// </summary>
    private static Kernel GetKernel()
    {
        return Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: "gpt-4o",
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();
    }

    #endregion
}

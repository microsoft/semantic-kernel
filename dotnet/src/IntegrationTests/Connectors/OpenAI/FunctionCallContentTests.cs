// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel;
using System.Collections.Generic;
using System.Threading.Tasks;
using Xunit;
using SemanticKernel.IntegrationTests.TestSettings;
using System;
using Microsoft.Extensions.Configuration;
using SemanticKernel.IntegrationTests.Planners.Stepwise;
using Xunit.Abstractions;
using System.Linq;
using System.Text.Json;

namespace SemanticKernel.IntegrationTests.Connectors.OpenAI;
public class FunctionCallContentTests : BaseIntegrationTest
{
    private readonly IConfigurationRoot _configuration;

    public FunctionCallContentTests(ITestOutputHelper output)
    {
        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<FunctionCallingStepwisePlannerTests>()
            .Build();
    }

    [Fact]
    public async Task ItCanHandleFunctionResultProvidedViaChatMessageContentOnlyAsync()
    {
        // Arrange
        var kernel = this.InitializeKernel();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

        var settings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        var completionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var result = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

        var toolCalls = ((OpenAIChatMessageContent)result).ToolCalls.OfType<ChatCompletionsFunctionToolCall>().ToList();

        while (toolCalls.Count > 0)
        {
            // Adding function call request from LLM to chat history
            chatHistory.Add(result);

            // Iterating over the requested function calls and invoking them
            foreach (var toolCall in toolCalls)
            {
                string content = kernel.Plugins.TryGetFunctionAndArguments(toolCall, out KernelFunction? function, out KernelArguments? arguments) ?
                    JsonSerializer.Serialize((await function.InvokeAsync(kernel, arguments)).GetValue<object>()) :
                    "Unable to find function. Please try again!";

                // Adding the result of the function call to the chat history
                chatHistory.Add(new ChatMessageContent(
                    AuthorRole.Tool,
                    content,
                    metadata: new Dictionary<string, object?>(1) { { OpenAIChatMessageContent.ToolIdProperty, toolCall.Id } }));
            }

            // Sending the functions execution results back to the LLM to get the final response
            result = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);
            toolCalls = ((OpenAIChatMessageContent)result).ToolCalls.OfType<ChatCompletionsFunctionToolCall>().ToList();
        }

        // Assert
        Assert.Contains("rain", result.Content, StringComparison.InvariantCultureIgnoreCase);
    }

    [Fact]
    public async Task ItCanHandleFunctionResultProvidedViaFunctionResultContentOfChatMessageContentHavingAToolRoleAsync()
    {
        // Arrange
        var kernel = this.InitializeKernel();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

        var settings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        var completionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

        var functionCalls = messageContent.Items.OfType<FunctionCallContent>().ToArray();

        while (functionCalls.Length > 0)
        {
            // Adding function call request from LLM to chat history
            chatHistory.Add(messageContent);

            // Iterating over the requested function calls and invoking them
            foreach (var functionCall in functionCalls)
            {
                var result = await functionCall.InvokeAsync(kernel);

                chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection { new FunctionResultContent(functionCall, result) }));
            }

            // Sending the functions execution results back to the LLM to get the final response
            messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);
            functionCalls = messageContent.Items.OfType<FunctionCallContent>().ToArray();
        }

        // Assert
        Assert.Contains("rain", messageContent.Content, StringComparison.InvariantCultureIgnoreCase);
    }

    [Fact]
    public async Task ItCanHandleExceptionsProvidedViaFunctionResultContentOfChatMessageContentHavingAToolRoleAsync()
    {
        // Arrange
        var kernel = this.InitializeKernel();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

        var settings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        var completionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

        var functionCalls = messageContent.Items.OfType<FunctionCallContent>().ToArray();

        while (functionCalls.Length > 0)
        {
            // Adding function call request from LLM to chat history
            chatHistory.Add(messageContent);

            // Iterating over the requested function calls and invoking them
            foreach (var functionCall in functionCalls)
            {
                // Simulating an exception
                var exception = new InvalidOperationException("An exception occurred while executing the function.");
                chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection { new FunctionResultContent(functionCall, exception) }));
            }

            // Sending the functions execution results back to the LLM to get the final response
            messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);
            functionCalls = messageContent.Items.OfType<FunctionCallContent>().ToArray();
        }

        // Assert
        Assert.NotNull(messageContent.Content);

        var failureWords = new List<string>() { "error", "unable", "couldn", "issue", "trouble" };
        Assert.Contains(failureWords, word => messageContent.Content.Contains(word, StringComparison.InvariantCultureIgnoreCase));
    }

    [Fact]
    public async Task ItCanHandleSimulatedFunctionsAsync()
    {
        // Arrange
        var kernel = this.InitializeKernel();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

        var settings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        var completionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

        var functionCalls = messageContent.Items.OfType<FunctionCallContent>().ToArray();

        while (functionCalls.Length > 0)
        {
            // Adding function call request from LLM to chat history
            chatHistory.Add(messageContent);

            // Iterating over the requested function calls and invoking them
            foreach (var functionCall in functionCalls)
            {
                var result = await functionCall.InvokeAsync(kernel);

                chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection { new FunctionResultContent(functionCall, result) }));
            }

            // Simulated function
            var simulatedFunctionCall = FunctionCallContent.Create("weather-alert", id: "call_123");
            messageContent.Items.Add(simulatedFunctionCall);

            var simulatedFunctionResult = "A Tornado Watch has been issued, with potential for severe thunderstorms causing unusual sky colors like green, yellow, or dark gray. Stay informed and follow safety instructions from authorities.";

            chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection {
                new FunctionResultContent(simulatedFunctionCall, simulatedFunctionResult)
            }));

            // Sending the functions execution results back to the LLM to get the final response
            messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);
            functionCalls = messageContent.Items.OfType<FunctionCallContent>().ToArray();
        }

        // Assert
        Assert.Contains("tornado", messageContent.Content, StringComparison.InvariantCultureIgnoreCase);
    }

    [Fact]
    public async Task ItShouldWrapSimulatedFunctionIntoSKFunctionAsync()
    {
        // Arrange
        var kernel = this.InitializeKernel();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

        var settings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        var completionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

        var functionCalls = messageContent.Items.OfType<FunctionCallContent>().ToArray();

        while (functionCalls.Length > 0)
        {
            // Adding function call request from LLM to chat history
            chatHistory.Add(messageContent);

            // Iterating over the requested function calls and invoking them
            foreach (var functionCall in functionCalls)
            {
                var result = await functionCall.InvokeAsync(kernel);

                chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection { new FunctionResultContent(functionCall, result) }));
            }

            //Simulated function

            // Registering function call
            var simulatedFunctionCall = FunctionCallContent.Create(pluginName: "weather", functionName: "alert", id: "call_DMkg2XDO1IDdv5c1lc8sAyGD");
            messageContent.Items.Add(simulatedFunctionCall);

            // Creating and executing the function
            var function = KernelFunctionFactory.CreateFromMethod(() => "A Tornado Watch has been issued, with potential for severe thunderstorms causing unusual sky colors like green, yellow, or dark gray. Stay informed and follow safety instructions from authorities.");

            var simulatedFunctionResult = await function.InvokeAsync(kernel);

            chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection { new FunctionResultContent(simulatedFunctionCall, simulatedFunctionResult) }));

            // Sending the functions execution results back to the LLM to get the final response
            messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);
            functionCalls = messageContent.Items.OfType<FunctionCallContent>().ToArray();
        }

        // Assert
        Assert.Contains("tornado", messageContent.Content, StringComparison.InvariantCultureIgnoreCase);
    }

    [Fact]
    public async Task ItFailsWhenFunctionResultProvidedViaBothChatMessageContentAndFunctionResultContentAsync()
    {
        // Arrange
        var kernel = this.InitializeKernel();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

        var settings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        var completionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

        chatHistory.Add(messageContent);

        // Iterating over the requested function calls and invoking them
        var toolCalls = ((OpenAIChatMessageContent)messageContent).ToolCalls.OfType<ChatCompletionsFunctionToolCall>().ToList();
        foreach (var toolCall in toolCalls)
        {
            string content = kernel.Plugins.TryGetFunctionAndArguments(toolCall, out KernelFunction? function, out KernelArguments? arguments) ?
                JsonSerializer.Serialize((await function.InvokeAsync(kernel, arguments)).GetValue<object>()) :
                "Unable to find function. Please try again!";

            // Adding the result of the function call to the chat history
            chatHistory.Add(new ChatMessageContent(
                AuthorRole.Tool,
                content,
                metadata: new Dictionary<string, object?>(1) { { OpenAIChatMessageContent.ToolIdProperty, toolCall.Id } }));
        }

        // Iterating over the requested function calls represented by function call content and invoking them
        var fcContents = messageContent.Items.OfType<FunctionCallContent>().ToArray();
        foreach (var functionCall in fcContents)
        {
            var result = await functionCall.InvokeAsync(kernel);

            chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection { new FunctionResultContent(functionCall, result) }));
        }

        // Act & Assert
        await Assert.ThrowsAsync<KernelException>(() => completionService.GetChatMessageContentAsync(chatHistory, settings, kernel));
    }

    [Fact]
    public async Task ItFailsWhenNoFunctionResultProvidedAsync()
    {
        // Arrange
        var kernel = this.InitializeKernel();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

        var settings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        var completionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var result = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

        chatHistory.Add(result);

        var exception = await Assert.ThrowsAsync<HttpOperationException>(() => completionService.GetChatMessageContentAsync(chatHistory, settings, kernel));

        // Assert
        Assert.Contains("'tool_calls' must be followed by tool", exception.Message, StringComparison.InvariantCulture);
    }

    [Fact]
    public async Task ItCanSerializeAndDeserializeChatHistoryWithFunctionResultContentAsync()
    {
        // Arrange
        var kernel = this.InitializeKernel();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

        var settings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        var completionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

        var functionCalls = messageContent.Items.OfType<FunctionCallContent>().ToArray();

        while (functionCalls.Length > 0)
        {
            // Adding function call request from LLM to chat history
            chatHistory.Add(messageContent);

            // Iterating over the requested function calls and invoking them
            foreach (var functionCall in functionCalls)
            {
                var result = await functionCall.InvokeAsync(kernel);

                chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection { new FunctionResultContent(functionCall, result) }));
            }

            // Simulated function
            var simulatedFunctionCall = FunctionCallContent.Create(pluginName: "weather", functionName: "alert", id: "call_DMkg2XDO1IDdv5c1lc8sAyGD");
            messageContent.Items.Add(simulatedFunctionCall);

            var simulatedFunctionResult = "A Tornado Watch has been issued, with potential for severe thunderstorms causing unusual sky colors like green, yellow, or dark gray. Stay informed and follow safety instructions from authorities.";

            chatHistory.Add(new ChatMessageContent(AuthorRole.Tool, new ChatMessageContentItemCollection {
                new FunctionResultContent(simulatedFunctionCall,simulatedFunctionResult)
            }));

            // Serializing chat history
            var serializedChatHistory = JsonSerializer.Serialize(chatHistory);

            // Deserializing chat history
            chatHistory = JsonSerializer.Deserialize<ChatHistory>(serializedChatHistory);

            // Explore deserialized function
            var resultAsJsonElement = chatHistory.ElementAt(2).Items.OfType<FunctionResultContent>().Single().Result;

            // Sending the functions execution results back to the LLM to get the final response
            messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);
            functionCalls = messageContent.Items.OfType<FunctionCallContent>().ToArray();
        }

        // Assert
        Assert.Contains("tornado", messageContent.Content, StringComparison.InvariantCultureIgnoreCase);
    }

    private Kernel InitializeKernel()
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        var openAIConfiguration = this._configuration.GetSection("Planners:OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        IKernelBuilder builder = this.CreateKernelBuilder()
            .AddOpenAIChatCompletion(
                modelId: openAIConfiguration.ModelId,
                apiKey: openAIConfiguration.ApiKey);

        var kernel = builder.Build();

        kernel.ImportPluginFromFunctions("HelperFunctions", new[]
        {
            kernel.CreateFunctionFromMethod(() => DateTime.UtcNow.ToString("R"), "GetCurrentUtcTime", "Retrieves the current time in UTC."),
            kernel.CreateFunctionFromMethod((string cityName) =>
                cityName switch
                {
                    "Boston" => "61 and rainy",
                    _ => "31 and snowing",
                }, "Get_Weather_For_City", "Gets the current weather for the specified city"),
        });

        return kernel;
    }
}

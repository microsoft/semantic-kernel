// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.Chat;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.AzureOpenAI;

public sealed class AzureOpenAIChatCompletionFunctionCallingTests : BaseIntegrationTest
{
    [Fact]
    public async Task CanAutoInvokeKernelFunctionsAsync()
    {
        // Arrange
        var invokedFunctions = new List<string>();

        var filter = new FakeFunctionFilter(async (context, next) =>
        {
            invokedFunctions.Add($"{context.Function.Name}({string.Join(", ", context.Arguments)})");
            await next(context);
        });

        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);
        kernel.FunctionInvocationFilters.Add(filter);

        AzureOpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        // Act
        var result = await kernel.InvokePromptAsync("Given the current time of day and weather, what is the likely color of the sky in Boston?", new(settings));

        // Assert
        Assert.Contains("GetCurrentUtcTime()", invokedFunctions);
        Assert.Contains("Get_Weather_For_City([cityName, Boston])", invokedFunctions);
    }

    [Fact]
    public async Task CanAutoInvokeKernelFunctionsStreamingAsync()
    {
        // Arrange
        var invokedFunctions = new List<string>();

        var filter = new FakeFunctionFilter(async (context, next) =>
        {
            invokedFunctions.Add($"{context.Function.Name}({string.Join(", ", context.Arguments)})");
            await next(context);
        });

        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);
        kernel.FunctionInvocationFilters.Add(filter);

        AzureOpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        var stringBuilder = new StringBuilder();

        // Act
        await foreach (var update in kernel.InvokePromptStreamingAsync<string>("Given the current time of day and weather, what is the likely color of the sky in Boston?", new(settings)))
        {
            stringBuilder.Append(update);
        }

        // Assert
        Assert.Contains("rain", stringBuilder.ToString(), StringComparison.InvariantCulture);
        Assert.Contains("GetCurrentUtcTime()", invokedFunctions);
        Assert.Contains("Get_Weather_For_City([cityName, Boston])", invokedFunctions);
    }

    [Fact]
    public async Task CanAutoInvokeKernelFunctionsWithComplexTypeParametersAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);

        AzureOpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        // Act
        var result = await kernel.InvokePromptAsync("What is the current temperature in Dublin, Ireland, in Fahrenheit?", new(settings));

        // Assert
        Assert.NotNull(result);
        Assert.Contains("42.8", result.GetValue<string>(), StringComparison.InvariantCulture); // The WeatherPlugin always returns 42.8 for Dublin, Ireland.
    }

    [Fact]
    public async Task CanAutoInvokeKernelFunctionsWithPrimitiveTypeParametersAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);

        AzureOpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        // Act
        var result = await kernel.InvokePromptAsync("Convert 50 degrees Fahrenheit to Celsius.", new(settings));

        // Assert
        Assert.NotNull(result);
        Assert.Contains("10", result.GetValue<string>(), StringComparison.InvariantCulture);
    }

    [Fact]
    public async Task CanAutoInvokeKernelFunctionsWithEnumTypeParametersAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);

        AzureOpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        // Act
        var result = await kernel.InvokePromptAsync("Given the current time of day and weather, what is the likely color of the sky in Boston?", new(settings));

        // Assert
        Assert.NotNull(result);
        Assert.Contains("rain", result.GetValue<string>(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task CanAutoInvokeKernelFunctionFromPromptAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var promptFunction = KernelFunctionFactory.CreateFromPrompt(
            "Your role is always to return this text - 'A Game-Changer for the Transportation Industry'. Don't ask for more details or context.",
            functionName: "FindLatestNews",
            description: "Searches for the latest news.");

        kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions(
            "NewsProvider",
            "Delivers up-to-date news content.",
            [promptFunction]));

        AzureOpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        // Act
        var result = await kernel.InvokePromptAsync("Show me the latest news as they are.", new(settings));

        // Assert
        Assert.NotNull(result);
        Assert.Contains("Transportation", result.GetValue<string>(), StringComparison.InvariantCultureIgnoreCase);
    }

    [Fact]
    public async Task CanAutoInvokeKernelFunctionFromPromptStreamingAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var promptFunction = KernelFunctionFactory.CreateFromPrompt(
            "Your role is always to return this text - 'A Game-Changer for the Transportation Industry'. Don't ask for more details or context.",
            functionName: "FindLatestNews",
            description: "Searches for the latest news.");

        kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions(
            "NewsProvider",
            "Delivers up-to-date news content.",
            [promptFunction]));

        AzureOpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        // Act
        var streamingResult = kernel.InvokePromptStreamingAsync("Show me the latest news as they are.", new(settings));

        var builder = new StringBuilder();

        await foreach (var update in streamingResult)
        {
            builder.Append(update.ToString());
        }

        var result = builder.ToString();

        // Assert
        Assert.NotNull(result);
        Assert.Contains("Transportation", result, StringComparison.InvariantCultureIgnoreCase);
    }

    [Fact]
    public async Task ConnectorSpecificChatMessageContentClassesCanBeUsedForManualFunctionCallingAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

        var settings = new AzureOpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        var sut = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var result = await sut.GetChatMessageContentAsync(chatHistory, settings, kernel);

        // Current way of handling function calls manually using connector specific chat message content class.
        var toolCalls = ((OpenAIChatMessageContent)result).ToolCalls.OfType<ChatToolCall>().ToList();

        while (toolCalls.Count > 0)
        {
            // Adding LLM function call request to chat history
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

            // Sending the functions invocation results back to the LLM to get the final response
            result = await sut.GetChatMessageContentAsync(chatHistory, settings, kernel);
            toolCalls = ((OpenAIChatMessageContent)result).ToolCalls.OfType<ChatToolCall>().ToList();
        }

        // Assert
        Assert.Contains("rain", result.Content, StringComparison.InvariantCultureIgnoreCase);
    }

    [Fact]
    public async Task ConnectorAgnosticFunctionCallingModelClassesCanBeUsedForManualFunctionCallingAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

        var settings = new AzureOpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        var sut = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var messageContent = await sut.GetChatMessageContentAsync(chatHistory, settings, kernel);

        var functionCalls = FunctionCallContent.GetFunctionCalls(messageContent).ToArray();

        while (functionCalls.Length != 0)
        {
            // Adding function call from LLM to chat history
            chatHistory.Add(messageContent);

            // Iterating over the requested function calls and invoking them
            foreach (var functionCall in functionCalls)
            {
                var result = await functionCall.InvokeAsync(kernel);

                chatHistory.Add(result.ToChatMessage());
            }

            // Sending the functions invocation results to the LLM to get the final response
            messageContent = await sut.GetChatMessageContentAsync(chatHistory, settings, kernel);
            functionCalls = FunctionCallContent.GetFunctionCalls(messageContent).ToArray();
        }

        // Assert
        Assert.Contains("rain", messageContent.Content, StringComparison.InvariantCultureIgnoreCase);
    }

    [Fact]
    public async Task ConnectorAgnosticFunctionCallingModelClassesCanPassFunctionExceptionToConnectorAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);

        var chatHistory = new ChatHistory();
        chatHistory.AddSystemMessage("Add the \"Error\" keyword to the response, if you are unable to answer a question or an error has happen.");
        chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

        var settings = new AzureOpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        var completionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

        var functionCalls = FunctionCallContent.GetFunctionCalls(messageContent).ToArray();

        while (functionCalls.Length != 0)
        {
            // Adding function call from LLM to chat history
            chatHistory.Add(messageContent);

            // Iterating over the requested function calls and invoking them
            foreach (var functionCall in functionCalls)
            {
                // Simulating an exception
                var exception = new OperationCanceledException("The operation was canceled due to timeout.");

                chatHistory.Add(new FunctionResultContent(functionCall, exception).ToChatMessage());
            }

            // Sending the functions execution results back to the LLM to get the final response
            messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);
            functionCalls = FunctionCallContent.GetFunctionCalls(messageContent).ToArray();
        }

        // Assert
        Assert.NotNull(messageContent.Content);
        TestHelpers.AssertChatErrorExcuseMessage(messageContent.Content);
    }

    [Fact]
    public async Task ConnectorAgnosticFunctionCallingModelClassesSupportSimulatedFunctionCallsAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);

        var chatHistory = new ChatHistory();
        chatHistory.AddSystemMessage("if there's a tornado warning, please add the 'tornado' keyword to the response.");
        chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

        var settings = new AzureOpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        var completionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

        var functionCalls = FunctionCallContent.GetFunctionCalls(messageContent).ToArray();

        while (functionCalls.Length > 0)
        {
            // Adding function call from LLM to chat history
            chatHistory.Add(messageContent);

            // Iterating over the requested function calls and invoking them
            foreach (var functionCall in functionCalls)
            {
                var result = await functionCall.InvokeAsync(kernel);

                chatHistory.AddMessage(AuthorRole.Tool, [result]);
            }

            // Adding a simulated function call to the connector response message
            var simulatedFunctionCall = new FunctionCallContent("weather-alert", id: "call_123");
            messageContent.Items.Add(simulatedFunctionCall);

            // Adding a simulated function result to chat history
            var simulatedFunctionResult = "A Tornado Watch has been issued, with potential for severe thunderstorms causing unusual sky colors like green, yellow, or dark gray. Stay informed and follow safety instructions from authorities.";
            chatHistory.Add(new FunctionResultContent(simulatedFunctionCall, simulatedFunctionResult).ToChatMessage());

            // Sending the functions invocation results back to the LLM to get the final response
            messageContent = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);
            functionCalls = FunctionCallContent.GetFunctionCalls(messageContent).ToArray();
        }

        // Assert
        Assert.Contains("tornado", messageContent.Content, StringComparison.InvariantCultureIgnoreCase);
    }

    [Fact]
    public async Task ItFailsIfNoFunctionResultProvidedAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

        var settings = new AzureOpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        var completionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var result = await completionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

        chatHistory.Add(result);

        var exception = await Assert.ThrowsAsync<HttpOperationException>(() => completionService.GetChatMessageContentAsync(chatHistory, settings, kernel));

        // Assert
        Assert.Contains("'tool_calls' must be followed by tool", exception.Message, StringComparison.InvariantCulture);
    }

    [Fact]
    public async Task ConnectorAgnosticFunctionCallingModelClassesCanBeUsedForAutoFunctionCallingAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

        var settings = new AzureOpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        var sut = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        await sut.GetChatMessageContentAsync(chatHistory, settings, kernel);

        // Assert
        var userMessage = chatHistory[0];
        Assert.Equal(AuthorRole.User, userMessage.Role);

        // LLM requested the functions to call.
        var getParallelFunctionCallRequestMessage = chatHistory[1];
        Assert.Equal(AuthorRole.Assistant, getParallelFunctionCallRequestMessage.Role);

        // Parallel Function Calls in the same request
        var functionCalls = getParallelFunctionCallRequestMessage.Items.OfType<FunctionCallContent>().ToArray();

        ChatMessageContent getCurrentTimeFunctionCallResultMessage;
        ChatMessageContent getWeatherForCityFunctionCallRequestMessage;
        FunctionCallContent getWeatherForCityFunctionCallRequest;
        FunctionCallContent getCurrentTimeFunctionCallRequest;
        ChatMessageContent getWeatherForCityFunctionCallResultMessage;

        // Assert
        // Non Parallel Tool Calling
        if (functionCalls.Length == 1)
        {
            // LLM requested the current time.
            getCurrentTimeFunctionCallRequest = functionCalls[0];

            // Connector invoked the GetCurrentUtcTime function and added result to chat history.
            getCurrentTimeFunctionCallResultMessage = chatHistory[2];

            // LLM requested the weather for Boston.
            getWeatherForCityFunctionCallRequestMessage = chatHistory[3];
            getWeatherForCityFunctionCallRequest = getWeatherForCityFunctionCallRequestMessage.Items.OfType<FunctionCallContent>().Single();

            // Connector invoked the Get_Weather_For_City function and added result to chat history.
            getWeatherForCityFunctionCallResultMessage = chatHistory[4];
        }
        else // Parallel Tool Calling
        {
            // LLM requested the current time.
            getCurrentTimeFunctionCallRequest = functionCalls[0];

            // LLM requested the weather for Boston.
            getWeatherForCityFunctionCallRequest = functionCalls[1];

            // Connector invoked the GetCurrentUtcTime function and added result to chat history.
            getCurrentTimeFunctionCallResultMessage = chatHistory[2];

            // Connector invoked the Get_Weather_For_City function and added result to chat history.
            getWeatherForCityFunctionCallResultMessage = chatHistory[3];
        }

        Assert.Equal("GetCurrentUtcTime", getCurrentTimeFunctionCallRequest.FunctionName);
        Assert.Equal("HelperFunctions", getCurrentTimeFunctionCallRequest.PluginName);
        Assert.NotNull(getCurrentTimeFunctionCallRequest.Id);

        Assert.Equal("Get_Weather_For_City", getWeatherForCityFunctionCallRequest.FunctionName);
        Assert.Equal("HelperFunctions", getWeatherForCityFunctionCallRequest.PluginName);
        Assert.NotNull(getWeatherForCityFunctionCallRequest.Id);

        Assert.Equal(AuthorRole.Tool, getCurrentTimeFunctionCallResultMessage.Role);
        Assert.Single(getCurrentTimeFunctionCallResultMessage.Items.OfType<TextContent>()); // Current function calling model adds TextContent item representing the result of the function call.

        var getCurrentTimeFunctionCallResult = getCurrentTimeFunctionCallResultMessage.Items.OfType<FunctionResultContent>().Single();
        // Connector invoked the GetCurrentUtcTime function and added result to chat history.
        Assert.Equal("GetCurrentUtcTime", getCurrentTimeFunctionCallResult.FunctionName);
        Assert.Equal("HelperFunctions", getCurrentTimeFunctionCallResult.PluginName);
        Assert.Equal(getCurrentTimeFunctionCallRequest.Id, getCurrentTimeFunctionCallResult.CallId);
        Assert.NotNull(getCurrentTimeFunctionCallResult.Result);

        Assert.Equal(AuthorRole.Tool, getWeatherForCityFunctionCallResultMessage.Role);
        Assert.Single(getWeatherForCityFunctionCallResultMessage.Items.OfType<TextContent>()); // Current function calling model adds TextContent item representing the result of the function call.

        var getWeatherForCityFunctionCallResult = getWeatherForCityFunctionCallResultMessage.Items.OfType<FunctionResultContent>().Single();
        Assert.Equal("Get_Weather_For_City", getWeatherForCityFunctionCallResult.FunctionName);
        Assert.Equal("HelperFunctions", getWeatherForCityFunctionCallResult.PluginName);
        Assert.Equal(getWeatherForCityFunctionCallRequest.Id, getWeatherForCityFunctionCallResult.CallId);
        Assert.NotNull(getWeatherForCityFunctionCallResult.Result);
    }

    [Fact]
    public async Task ConnectorAgnosticFunctionCallingModelClassesCanBeUsedForManualFunctionCallingForStreamingAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);

        var settings = new AzureOpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        var sut = kernel.GetRequiredService<IChatCompletionService>();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

        string? result = null;

        // Act
        while (true)
        {
            AuthorRole? authorRole = null;
            var fccBuilder = new FunctionCallContentBuilder();
            var textContent = new StringBuilder();

            await foreach (var streamingContent in sut.GetStreamingChatMessageContentsAsync(chatHistory, settings, kernel))
            {
                textContent.Append(streamingContent.Content);
                authorRole ??= streamingContent.Role;
                fccBuilder.Append(streamingContent);
            }

            var functionCalls = fccBuilder.Build();
            if (functionCalls.Any())
            {
                var fcContent = new ChatMessageContent(role: authorRole ?? default, content: null);
                chatHistory.Add(fcContent);

                // Iterating over the requested function calls and invoking them
                foreach (var functionCall in functionCalls)
                {
                    fcContent.Items.Add(functionCall);

                    var functionResult = await functionCall.InvokeAsync(kernel);

                    chatHistory.Add(functionResult.ToChatMessage());
                }

                continue;
            }

            result = textContent.ToString();
            break;
        }

        // Assert
        Assert.Contains("rain", result, StringComparison.InvariantCultureIgnoreCase);
    }

    [Fact]
    public async Task ConnectorAgnosticFunctionCallingModelClassesCanBeUsedForAutoFunctionCallingForStreamingAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

        var settings = new AzureOpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        var sut = kernel.GetRequiredService<IChatCompletionService>();

        var result = new StringBuilder();

        // Act
        await foreach (var contentUpdate in sut.GetStreamingChatMessageContentsAsync(chatHistory, settings, kernel))
        {
            result.Append(contentUpdate.Content);
        }

        // Assert
        var userMessage = chatHistory[0];
        Assert.Equal(AuthorRole.User, userMessage.Role);

        // LLM requested the functions to call.
        var getParallelFunctionCallRequestMessage = chatHistory[1];
        Assert.Equal(AuthorRole.Assistant, getParallelFunctionCallRequestMessage.Role);

        // Parallel Function Calls in the same request
        var functionCalls = getParallelFunctionCallRequestMessage.Items.OfType<FunctionCallContent>().ToArray();

        ChatMessageContent getCurrentTimeFunctionCallResultMessage;
        ChatMessageContent getWeatherForCityFunctionCallRequestMessage;
        FunctionCallContent getWeatherForCityFunctionCallRequest;
        FunctionCallContent getCurrentTimeFunctionCallRequest;
        ChatMessageContent getWeatherForCityFunctionCallResultMessage;

        // Assert
        // Non Parallel Tool Calling
        if (functionCalls.Length == 1)
        {
            // LLM requested the current time.
            getCurrentTimeFunctionCallRequest = functionCalls[0];

            // Connector invoked the GetCurrentUtcTime function and added result to chat history.
            getCurrentTimeFunctionCallResultMessage = chatHistory[2];

            // LLM requested the weather for Boston.
            getWeatherForCityFunctionCallRequestMessage = chatHistory[3];
            getWeatherForCityFunctionCallRequest = getWeatherForCityFunctionCallRequestMessage.Items.OfType<FunctionCallContent>().Single();

            // Connector invoked the Get_Weather_For_City function and added result to chat history.
            getWeatherForCityFunctionCallResultMessage = chatHistory[4];
        }
        else // Parallel Tool Calling
        {
            // LLM requested the current time.
            getCurrentTimeFunctionCallRequest = functionCalls[0];

            // LLM requested the weather for Boston.
            getWeatherForCityFunctionCallRequest = functionCalls[1];

            // Connector invoked the GetCurrentUtcTime function and added result to chat history.
            getCurrentTimeFunctionCallResultMessage = chatHistory[2];

            // Connector invoked the Get_Weather_For_City function and added result to chat history.
            getWeatherForCityFunctionCallResultMessage = chatHistory[3];
        }

        Assert.Equal("GetCurrentUtcTime", getCurrentTimeFunctionCallRequest.FunctionName);
        Assert.Equal("HelperFunctions", getCurrentTimeFunctionCallRequest.PluginName);
        Assert.NotNull(getCurrentTimeFunctionCallRequest.Id);

        Assert.Equal("Get_Weather_For_City", getWeatherForCityFunctionCallRequest.FunctionName);
        Assert.Equal("HelperFunctions", getWeatherForCityFunctionCallRequest.PluginName);
        Assert.NotNull(getWeatherForCityFunctionCallRequest.Id);

        Assert.Equal(AuthorRole.Tool, getCurrentTimeFunctionCallResultMessage.Role);
        Assert.Single(getCurrentTimeFunctionCallResultMessage.Items.OfType<TextContent>()); // Current function calling model adds TextContent item representing the result of the function call.

        var getCurrentTimeFunctionCallResult = getCurrentTimeFunctionCallResultMessage.Items.OfType<FunctionResultContent>().Single();
        // Connector invoked the GetCurrentUtcTime function and added result to chat history.
        Assert.Equal("GetCurrentUtcTime", getCurrentTimeFunctionCallResult.FunctionName);
        Assert.Equal("HelperFunctions", getCurrentTimeFunctionCallResult.PluginName);
        Assert.Equal(getCurrentTimeFunctionCallRequest.Id, getCurrentTimeFunctionCallResult.CallId);
        Assert.NotNull(getCurrentTimeFunctionCallResult.Result);

        Assert.Equal(AuthorRole.Tool, getWeatherForCityFunctionCallResultMessage.Role);
        Assert.Single(getWeatherForCityFunctionCallResultMessage.Items.OfType<TextContent>()); // Current function calling model adds TextContent item representing the result of the function call.

        var getWeatherForCityFunctionCallResult = getWeatherForCityFunctionCallResultMessage.Items.OfType<FunctionResultContent>().Single();
        Assert.Equal("Get_Weather_For_City", getWeatherForCityFunctionCallResult.FunctionName);
        Assert.Equal("HelperFunctions", getWeatherForCityFunctionCallResult.PluginName);
        Assert.Equal(getWeatherForCityFunctionCallRequest.Id, getWeatherForCityFunctionCallResult.CallId);
        Assert.NotNull(getWeatherForCityFunctionCallResult.Result);
    }

    [Fact]
    public async Task ConnectorAgnosticFunctionCallingModelClassesCanPassFunctionExceptionToConnectorForStreamingAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);

        var settings = new AzureOpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        var sut = kernel.GetRequiredService<IChatCompletionService>();

        var chatHistory = new ChatHistory();
        chatHistory.AddSystemMessage("Add the \"Error\" keyword to the response, if you are unable to answer a question or an error has happen.");
        chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

        string? result = null;

        // Act
        while (true)
        {
            AuthorRole? authorRole = null;
            var fccBuilder = new FunctionCallContentBuilder();
            var textContent = new StringBuilder();

            await foreach (var streamingContent in sut.GetStreamingChatMessageContentsAsync(chatHistory, settings, kernel))
            {
                textContent.Append(streamingContent.Content);
                authorRole ??= streamingContent.Role;
                fccBuilder.Append(streamingContent);
            }

            var functionCalls = fccBuilder.Build();
            if (functionCalls.Any())
            {
                var fcContent = new ChatMessageContent(role: authorRole ?? default, content: null);
                chatHistory.Add(fcContent);

                // Iterating over the requested function calls and invoking them
                foreach (var functionCall in functionCalls)
                {
                    fcContent.Items.Add(functionCall);

                    // Simulating an exception
                    var exception = new OperationCanceledException("The operation was canceled due to timeout.");

                    chatHistory.Add(new FunctionResultContent(functionCall, exception).ToChatMessage());
                }

                continue;
            }

            result = textContent.ToString();
            break;
        }

        // Assert
        TestHelpers.AssertChatErrorExcuseMessage(result);
    }

    [Fact]
    public async Task ConnectorAgnosticFunctionCallingModelClassesSupportSimulatedFunctionCallsForStreamingAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);

        var settings = new AzureOpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions };

        var sut = kernel.GetRequiredService<IChatCompletionService>();

        var chatHistory = new ChatHistory();
        chatHistory.AddSystemMessage("if there's a tornado warning, please add the 'tornado' keyword to the response.");
        chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

        string? result = null;

        // Act
        while (true)
        {
            AuthorRole? authorRole = null;
            var fccBuilder = new FunctionCallContentBuilder();
            var textContent = new StringBuilder();

            await foreach (var streamingContent in sut.GetStreamingChatMessageContentsAsync(chatHistory, settings, kernel))
            {
                textContent.Append(streamingContent.Content);
                authorRole ??= streamingContent.Role;
                fccBuilder.Append(streamingContent);
            }

            var functionCalls = fccBuilder.Build();
            if (functionCalls.Any())
            {
                var fcContent = new ChatMessageContent(role: authorRole ?? default, content: null);
                chatHistory.Add(fcContent);

                // Iterating over the requested function calls and invoking them
                foreach (var functionCall in functionCalls)
                {
                    fcContent.Items.Add(functionCall);

                    var functionResult = await functionCall.InvokeAsync(kernel);

                    chatHistory.Add(functionResult.ToChatMessage());
                }

                // Adding a simulated function call to the connector response message
                var simulatedFunctionCall = new FunctionCallContent("weather-alert", id: "call_123");
                fcContent.Items.Add(simulatedFunctionCall);

                // Adding a simulated function result to chat history
                var simulatedFunctionResult = "A Tornado Watch has been issued, with potential for severe thunderstorms causing unusual sky colors like green, yellow, or dark gray. Stay informed and follow safety instructions from authorities.";
                chatHistory.Add(new FunctionResultContent(simulatedFunctionCall, simulatedFunctionResult).ToChatMessage());

                continue;
            }

            result = textContent.ToString();
            break;
        }

        // Assert
        Assert.Contains("tornado", result, StringComparison.InvariantCultureIgnoreCase);
    }

    [Fact]
    public async Task ItShouldSupportOldFunctionCallingModelSerializedIntoChatHistoryByPreviousVersionOfSKAsync()
    {
        // Arrange
        var chatHistory = JsonSerializer.Deserialize<ChatHistory>(File.ReadAllText("./TestData/serializedChatHistoryV1_15_1.json"));

        // Remove connector-agnostic function-calling items to check if the old function-calling model, which relies on function information in metadata, is handled correctly.
        foreach (var chatMessage in chatHistory!)
        {
            var index = 0;
            while (index < chatMessage.Items.Count)
            {
                var item = chatMessage.Items[index];
                if (item is FunctionCallContent || item is FunctionResultContent)
                {
                    chatMessage.Items.Remove(item);
                    continue;
                }
                index++;
            }
        }

        string? emailBody = null, emailRecipient = null;

        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);
        kernel.ImportPluginFromFunctions("EmailPlugin", [KernelFunctionFactory.CreateFromMethod((string body, string recipient) => { emailBody = body; emailRecipient = recipient; }, "SendEmail")]);

        // The deserialized chat history contains a list of function calls and the final answer to the question regarding the color of the sky in Boston.
        chatHistory.AddUserMessage("Send the exact answer to my email: abc@domain.com");

        var settings = new AzureOpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        // Act
        var result = await kernel.GetRequiredService<IChatCompletionService>().GetChatMessageContentAsync(chatHistory, settings, kernel);

        // Assert
        Assert.Equal("abc@domain.com", emailRecipient);
        Assert.Contains("61\u00B0F", emailBody);
    }

    [Fact]
    public async Task ItShouldSupportNewFunctionCallingModelSerializedIntoChatHistoryByPreviousVersionOfSKAsync()
    {
        // Arrange
        var chatHistory = JsonSerializer.Deserialize<ChatHistory>(File.ReadAllText("./TestData/serializedChatHistoryV1_15_1.json"));

        // Remove metadata related to the old function-calling model to check if the new model, which relies on function call content/result classes, is handled correctly.
        foreach (var chatMessage in chatHistory!)
        {
            if (chatMessage.Metadata is not null)
            {
                var metadata = new Dictionary<string, object?>(chatMessage.Metadata);
                metadata.Remove(OpenAIChatMessageContent.ToolIdProperty);
                metadata.Remove("ChatResponseMessage.FunctionToolCalls");
                chatMessage.Metadata = metadata;
            }
        }

        string? emailBody = null, emailRecipient = null;

        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);
        kernel.ImportPluginFromFunctions("EmailPlugin", [KernelFunctionFactory.CreateFromMethod((string body, string recipient) => { emailBody = body; emailRecipient = recipient; }, "SendEmail")]);

        // The deserialized chat history contains a list of function calls and the final answer to the question regarding the color of the sky in Boston.
        chatHistory.AddUserMessage("Send the exact answer to my email: abc@domain.com");

        var settings = new AzureOpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        // Act
        var result = await kernel.GetRequiredService<IChatCompletionService>().GetChatMessageContentAsync(chatHistory, settings, kernel);

        // Assert
        Assert.Equal("abc@domain.com", emailRecipient);
        Assert.Contains("61\u00B0F", emailBody);
    }

    /// <summary>
    /// This test verifies that the connector can handle the scenario where the assistant response message is added to the chat history.
    /// The assistant response message with no function calls added to chat history caused the error: HTTP 400 (invalid_request_error:) [] should be non-empty - 'messages.3.tool_calls'
    /// </summary>
    [Fact]
    public async Task AssistantResponseAddedToChatHistoryShouldBeHandledCorrectlyAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel(importHelperPlugin: true);

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Given the current time of day and weather, what is the likely color of the sky in Boston?");

        var settings = new AzureOpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        var sut = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var assistanceResponse = await sut.GetChatMessageContentAsync(chatHistory, settings, kernel);

        chatHistory.Add(assistanceResponse); // Adding assistance response to chat history.
        chatHistory.AddUserMessage("Return only the color name.");

        await sut.GetChatMessageContentAsync(chatHistory, settings, kernel);
    }

    private Kernel CreateAndInitializeKernel(bool importHelperPlugin = false)
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);
        Assert.NotNull(azureOpenAIConfiguration.ChatDeploymentName);
        Assert.NotNull(azureOpenAIConfiguration.ApiKey);
        Assert.NotNull(azureOpenAIConfiguration.Endpoint);

        var kernelBuilder = base.CreateKernelBuilder();

        kernelBuilder.AddAzureOpenAIChatCompletion(
            deploymentName: azureOpenAIConfiguration.ChatDeploymentName,
            modelId: azureOpenAIConfiguration.ChatModelId,
            endpoint: azureOpenAIConfiguration.Endpoint,
            apiKey: azureOpenAIConfiguration.ApiKey);

        var kernel = kernelBuilder.Build();

        if (importHelperPlugin)
        {
            kernel.ImportPluginFromFunctions("HelperFunctions",
            [
                kernel.CreateFunctionFromMethod(() => DateTime.UtcNow.ToString("R"), "GetCurrentUtcTime", "Retrieves the current time in UTC."),
                kernel.CreateFunctionFromMethod((string cityName) =>
                {
                    return cityName switch
                    {
                        "Boston" => "61 and rainy",
                        _ => "31 and snowing",
                    };
                }, "Get_Weather_For_City", "Gets the current weather for the specified city"),
                kernel.CreateFunctionFromMethod((WeatherParameters parameters) =>
                {
                    if (parameters.City.Name == "Dublin" && (parameters.City.Country == "Ireland" || parameters.City.Country == "IE"))
                    {
                        return Task.FromResult(42.8); // 42.8 Fahrenheit.
                    }

                    throw new NotSupportedException($"Weather in {parameters.City.Name} ({parameters.City.Country}) is not supported.");
                }, "Get_Current_Temperature", "Get current temperature."),
                kernel.CreateFunctionFromMethod((double temperatureInFahrenheit) =>
                {
                    double temperatureInCelsius = (temperatureInFahrenheit - 32) * 5 / 9;
                    return Task.FromResult(temperatureInCelsius);
                }, "Convert_Temperature_From_Fahrenheit_To_Celsius", "Convert temperature from Fahrenheit to Celsius.")
            ]);
        }

        return kernel;
    }

    public record WeatherParameters(City City);

    public class City
    {
        public string Name { get; set; } = string.Empty;
        public string Country { get; set; } = string.Empty;
    }

    private sealed class FakeFunctionFilter : IFunctionInvocationFilter
    {
        private readonly Func<FunctionInvocationContext, Func<FunctionInvocationContext, Task>, Task>? _onFunctionInvocation;

        public FakeFunctionFilter(
            Func<FunctionInvocationContext, Func<FunctionInvocationContext, Task>, Task>? onFunctionInvocation = null)
        {
            this._onFunctionInvocation = onFunctionInvocation;
        }

        public Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next) =>
            this._onFunctionInvocation?.Invoke(context, next) ?? Task.CompletedTask;
    }

    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<AzureOpenAIChatCompletionTests>()
        .Build();
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.MistralAI;
using Xunit;

namespace SemanticKernel.Connectors.MistralAI.UnitTests.Services;

/// <summary>
/// Unit tests for <see cref="MistralAIChatCompletionService"/>.
/// </summary>
public sealed class MistralAIChatCompletionServiceTests : MistralTestBase
{
    [Fact]
    public async Task ValidateGetChatMessageContentsAsync()
    {
        // Arrange
        var content = this.GetTestResponseAsString("chat_completions_response.json");
        this.DelegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", content);
        this.HttpClient = new HttpClient(this.DelegatingHandler, false);
        var service = new MistralAIChatCompletionService("mistral-small-latest", "key", httpClient: this.HttpClient);

        // Act
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the best French cheese?")
        };
        var response = await service.GetChatMessageContentsAsync(chatHistory, default);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Equal("I don't have a favorite condiment as I don't consume food or condiments. However, I can tell you that many people enjoy using ketchup, mayonnaise, hot sauce, soy sauce, or mustard as condiments to enhance the flavor of their meals. Some people also enjoy using herbs, spices, or vinegars as condiments. Ultimately, the best condiment is a matter of personal preference.", response[0].Content);
    }

    [Fact]
    public async Task ValidateGetStreamingChatMessageContentsAsync()
    {
        // Arrange
        var content = this.GetTestResponseAsBytes("chat_completions_streaming_response.txt");
        this.DelegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", true, content);
        this.HttpClient = new HttpClient(this.DelegatingHandler, false);
        var service = new MistralAIChatCompletionService("mistral-small-latest", "key", httpClient: this.HttpClient);

        // Act
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the best French cheese?")
        };
        var response = service.GetStreamingChatMessageContentsAsync(chatHistory, default);
        var chunks = new List<StreamingChatMessageContent>();
        await foreach (var chunk in response)
        {
            chunks.Add(chunk);
        }

        // Assert
        Assert.NotNull(response);
        Assert.Equal(124, chunks.Count);
        foreach (var chunk in chunks)
        {
            Assert.NotNull(chunk);
            Assert.Equal("mistral-small-latest", chunk.ModelId);
            Assert.NotNull(chunk.Content);
            Assert.NotNull(chunk.Role);
            Assert.NotNull(chunk.Metadata);
        }
    }

    [Fact]
    public async Task GetChatMessageContentShouldSendMutatedChatHistoryToLLMAsync()
    {
        // Arrange
        static Task MutateChatHistoryAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            // Remove the function call messages from the chat history to reduce token count.
            context.ChatHistory.RemoveRange(1, 2); // Remove the `Date` function call and function result messages.

            return next(context);
        }

        var kernel = new Kernel();
        kernel.ImportPluginFromFunctions("WeatherPlugin", [KernelFunctionFactory.CreateFromMethod((string location) => "rainy", "GetWeather")]);
        kernel.AutoFunctionInvocationFilters.Add(new AutoFunctionInvocationFilter(MutateChatHistoryAsync));

        var firstResponse = this.GetTestResponseAsBytes("chat_completions_function_call_response.json");
        var secondResponse = this.GetTestResponseAsBytes("chat_completions_function_called_response.json");

        this.DelegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", false, firstResponse, secondResponse);
        this.HttpClient = new HttpClient(this.DelegatingHandler, false);

        var sut = new MistralAIChatCompletionService("mistral-small-latest", "key", httpClient: this.HttpClient);

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What time is it?"),
            new ChatMessageContent(AuthorRole.Assistant, [
                new FunctionCallContent("Date", "TimePlugin", "2")
            ]),
            new ChatMessageContent(AuthorRole.Tool, [
                new FunctionResultContent("Date",  "TimePlugin", "2", "rainy")
            ]),
            new ChatMessageContent(AuthorRole.Assistant, "08/06/2024 00:00:00"),
            new ChatMessageContent(AuthorRole.User, "Given the current time of day and weather, what is the likely color of the sky in Boston?")
        };

        // Act
        await sut.GetChatMessageContentAsync(chatHistory, new MistralAIPromptExecutionSettings() { ToolCallBehavior = MistralAIToolCallBehavior.AutoInvokeKernelFunctions }, kernel);

        // Assert
        var actualRequestContent = this.DelegatingHandler.RequestContent!;
        Assert.NotNull(actualRequestContent);

        var optionsJson = JsonElement.Parse(actualRequestContent);

        var messages = optionsJson.GetProperty("messages");
        Assert.Equal(5, messages.GetArrayLength());

        var userFirstPrompt = messages[0];
        Assert.Equal("user", userFirstPrompt.GetProperty("role").GetString());
        Assert.Equal("What time is it?", userFirstPrompt.GetProperty("content").ToString());

        var assistantFirstResponse = messages[1];
        Assert.Equal("assistant", assistantFirstResponse.GetProperty("role").GetString());
        Assert.Equal("08/06/2024 00:00:00", assistantFirstResponse.GetProperty("content").GetString());

        var userSecondPrompt = messages[2];
        Assert.Equal("user", userSecondPrompt.GetProperty("role").GetString());
        Assert.Equal("Given the current time of day and weather, what is the likely color of the sky in Boston?", userSecondPrompt.GetProperty("content").ToString());

        var assistantSecondResponse = messages[3];
        Assert.Equal("assistant", assistantSecondResponse.GetProperty("role").GetString());
        Assert.Equal("ejOH4Z1A2", assistantSecondResponse.GetProperty("tool_calls")[0].GetProperty("id").GetString());
        Assert.Equal("WeatherPlugin-GetWeather", assistantSecondResponse.GetProperty("tool_calls")[0].GetProperty("function").GetProperty("name").GetString());
        Assert.Equal("function", assistantSecondResponse.GetProperty("tool_calls")[0].GetProperty("type").GetString());

        var functionResult = messages[4];
        Assert.Equal("tool", functionResult.GetProperty("role").GetString());
        Assert.Equal("rainy", functionResult.GetProperty("content").GetString());
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsShouldSendMutatedChatHistoryToLLMAsync()
    {
        // Arrange
        static Task MutateChatHistory(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            // Remove the function call messages from the chat history to reduce token count.
            context.ChatHistory.RemoveRange(1, 2); // Remove the `Date` function call and function result messages.

            return next(context);
        }

        var kernel = new Kernel();
        kernel.ImportPluginFromFunctions("WeatherPlugin", [KernelFunctionFactory.CreateFromMethod(() => "rainy", "GetWeather")]);
        kernel.AutoFunctionInvocationFilters.Add(new AutoFunctionInvocationFilter(MutateChatHistory));

        var firstResponse = this.GetTestResponseAsBytes("chat_completions_streaming_function_call_response.txt");
        var secondResponse = this.GetTestResponseAsBytes("chat_completions_streaming_function_called_response.txt");

        this.DelegatingHandler = new AssertingDelegatingHandler("https://api.mistral.ai/v1/chat/completions", true, firstResponse, secondResponse);
        this.HttpClient = new HttpClient(this.DelegatingHandler, false);

        var sut = new MistralAIChatCompletionService("mistral-small-latest", "key", httpClient: this.HttpClient);

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What time is it?"),
            new ChatMessageContent(AuthorRole.Assistant, [
                new FunctionCallContent("Date", "TimePlugin", "2")
            ]),
            new ChatMessageContent(AuthorRole.Tool, [
                new FunctionResultContent("Date",  "TimePlugin", "2", "rainy")
            ]),
            new ChatMessageContent(AuthorRole.Assistant, "08/06/2024 00:00:00"),
            new ChatMessageContent(AuthorRole.User, "Given the current time of day and weather, what is the likely color of the sky in Boston?")
        };

        // Act
        await foreach (var update in sut.GetStreamingChatMessageContentsAsync(chatHistory, new MistralAIPromptExecutionSettings() { ToolCallBehavior = MistralAIToolCallBehavior.AutoInvokeKernelFunctions }, kernel))
        {
        }

        // Assert
        var actualRequestContent = this.DelegatingHandler.RequestContent!;
        Assert.NotNull(actualRequestContent);

        var optionsJson = JsonElement.Parse(actualRequestContent);

        var messages = optionsJson.GetProperty("messages");
        Assert.Equal(5, messages.GetArrayLength());

        var userFirstPrompt = messages[0];
        Assert.Equal("user", userFirstPrompt.GetProperty("role").GetString());
        Assert.Equal("What time is it?", userFirstPrompt.GetProperty("content").ToString());

        var assistantFirstResponse = messages[1];
        Assert.Equal("assistant", assistantFirstResponse.GetProperty("role").GetString());
        Assert.Equal("08/06/2024 00:00:00", assistantFirstResponse.GetProperty("content").GetString());

        var userSecondPrompt = messages[2];
        Assert.Equal("user", userSecondPrompt.GetProperty("role").GetString());
        Assert.Equal("Given the current time of day and weather, what is the likely color of the sky in Boston?", userSecondPrompt.GetProperty("content").ToString());

        var assistantSecondResponse = messages[3];
        Assert.Equal("assistant", assistantSecondResponse.GetProperty("role").GetString());
        Assert.Equal("u2ef3Udel", assistantSecondResponse.GetProperty("tool_calls")[0].GetProperty("id").GetString());
        Assert.Equal("WeatherPlugin-GetWeather", assistantSecondResponse.GetProperty("tool_calls")[0].GetProperty("function").GetProperty("name").GetString());
        Assert.Equal("function", assistantSecondResponse.GetProperty("tool_calls")[0].GetProperty("type").GetString());

        var functionResult = messages[4];
        Assert.Equal("tool", functionResult.GetProperty("role").GetString());
        Assert.Equal("rainy", functionResult.GetProperty("content").GetString());
    }

    private sealed class AutoFunctionInvocationFilter : IAutoFunctionInvocationFilter
    {
        private readonly Func<AutoFunctionInvocationContext, Func<AutoFunctionInvocationContext, Task>, Task> _callback;

        public AutoFunctionInvocationFilter(Func<AutoFunctionInvocationContext, Func<AutoFunctionInvocationContext, Task>, Task> callback)
        {
            Verify.NotNull(callback, nameof(callback));
            this._callback = callback;
        }

        public AutoFunctionInvocationFilter(Action<AutoFunctionInvocationContext, Func<AutoFunctionInvocationContext, Task>> callback)
        {
            Verify.NotNull(callback, nameof(callback));
            this._callback = (c, n) => { callback(c, n); return Task.CompletedTask; };
        }

        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            await this._callback(context, next);
        }
    }
}

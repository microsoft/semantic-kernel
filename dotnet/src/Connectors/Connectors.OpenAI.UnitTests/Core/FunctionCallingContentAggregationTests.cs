// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Core;

/// <summary>
/// Tests for non-streaming function calling content and usage aggregation.
/// Verifies that text content generated before tool calls is preserved and that
/// token usage is correctly summed across all API calls in the function calling loop.
/// </summary>
public sealed class FunctionCallingContentAggregationTests : IDisposable
{
    private readonly MultipleHttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public FunctionCallingContentAggregationTests()
    {
        this._messageHandlerStub = new MultipleHttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task NonStreaming_IntermediateTextBeforeToolCall_IsAggregatedInFinalResponseAsync()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod((string parameter) => "function-result", "Function1");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function]);
        var kernel = this.CreateKernel(plugin);

        // First response: LLM generates text AND a tool call
        // Second response: LLM generates final text after function execution
        this._messageHandlerStub.ResponsesToReturn = GetTextWithToolCallResponses();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What is the answer?");

        var settings = new OpenAIPromptExecutionSettings
        {
            ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions
        };

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var result = await chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Content);

        // The final content should contain BOTH the intermediate text and the final response
        Assert.Contains("Let me check that for you", result.Content);
        Assert.Contains("Based on my research, the answer is 42", result.Content);
    }

    [Fact]
    public async Task NonStreaming_TokenUsage_IsAggregatedAcrossAllIterationsAsync()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod((string parameter) => "function-result", "Function1");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function]);
        var kernel = this.CreateKernel(plugin);

        this._messageHandlerStub.ResponsesToReturn = GetTextWithToolCallResponses();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What is the answer?");

        var settings = new OpenAIPromptExecutionSettings
        {
            ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions
        };

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var result = await chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Metadata);

        // Verify aggregated usage is present
        // First call: 100 prompt + 50 completion = 150 total
        // Second call: 200 prompt + 25 completion = 225 total
        // Aggregated: 300 prompt + 75 completion = 375 total
        Assert.True(result.Metadata.ContainsKey("AggregatedUsage"), "Metadata should contain AggregatedUsage");

        var aggregatedUsage = result.Metadata["AggregatedUsage"] as Dictionary<string, int>;
        Assert.NotNull(aggregatedUsage);
        Assert.Equal(300, aggregatedUsage["InputTokens"]);
        Assert.Equal(75, aggregatedUsage["OutputTokens"]);
        Assert.Equal(375, aggregatedUsage["TotalTokens"]);
    }

    [Fact]
    public async Task NonStreaming_SingleIteration_NoAggregationMetadataAddedAsync()
    {
        // Arrange - No function, so only one API call
        var kernel = this.CreateKernel(plugin: null);

        this._messageHandlerStub.ResponsesToReturn =
        [
            new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StreamContent(File.OpenRead("TestData/chat_completion_test_response.json"))
            }
        ];

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");

        var settings = new OpenAIPromptExecutionSettings();

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var result = await chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Test chat response", result.Content);

        // Single iteration should NOT have AggregatedUsage metadata
        Assert.False(
            result.Metadata?.ContainsKey("AggregatedUsage") ?? false,
            "Single iteration should not have AggregatedUsage metadata");
    }

    [Fact]
    public async Task NonStreaming_ToolCallWithoutIntermediateText_OnlyFinalTextReturnedAsync()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod((string parameter) => "function-result", "Function1");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function]);
        var kernel = this.CreateKernel(plugin);

        // First response: tool call without text content (content: null)
        // Second response: final text
        this._messageHandlerStub.ResponsesToReturn = GetToolCallWithoutTextResponses();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What is the answer?");

        var settings = new OpenAIPromptExecutionSettings
        {
            ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions
        };

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var result = await chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Based on my research, the answer is 42.", result.Content);
    }

    [Fact]
    public async Task NonStreaming_FilterTerminatesEarly_AggregatedContentStillAppliedAsync()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod((string parameter) => "function-result", "Function1");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function]);

        var builder = Kernel.CreateBuilder();
        builder.Plugins.Add(plugin);

        // Add filter that terminates after first function call
        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(new TerminatingFilter());
        builder.Services.AddSingleton<IChatCompletionService>(
            _ => new OpenAIChatCompletionService("model-id", "test-api-key", "organization-id", this._httpClient));

        var kernel = builder.Build();

        this._messageHandlerStub.ResponsesToReturn = GetTextWithToolCallResponses();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What is the answer?");

        var settings = new OpenAIPromptExecutionSettings
        {
            ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions
        };

        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // Act
        var result = await chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, kernel);

        // Assert
        Assert.NotNull(result);

        // Even though filter terminated early, the intermediate text from the first iteration
        // (generated before the tool call) should be preserved in the result.
        // The first API response contained: "Let me check that for you. I'll look up the current information."
        Assert.NotNull(result.Content);
        Assert.Contains("Let me check that for you", result.Content);

        // The second API call should NOT have been made (filter terminated),
        // so the final response text should NOT be present.
        Assert.DoesNotContain("Based on my research", result.Content);

        // Verify aggregated usage contains tokens from the first iteration only.
        // First call: 100 prompt + 50 completion tokens
        Assert.NotNull(result.Metadata);
        Assert.True(result.Metadata.ContainsKey("AggregatedUsage"), "Metadata should contain AggregatedUsage even when filter terminates");

        var aggregatedUsage = result.Metadata["AggregatedUsage"] as Dictionary<string, int>;
        Assert.NotNull(aggregatedUsage);
        Assert.Equal(100, aggregatedUsage["InputTokens"]);
        Assert.Equal(50, aggregatedUsage["OutputTokens"]);
        Assert.Equal(150, aggregatedUsage["TotalTokens"]);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }

    #region Private Helpers

    private Kernel CreateKernel(KernelPlugin? plugin)
    {
        var builder = Kernel.CreateBuilder();

        if (plugin is not null)
        {
            builder.Plugins.Add(plugin);
        }

        builder.Services.AddSingleton<IChatCompletionService>(
            _ => new OpenAIChatCompletionService("model-id", "test-api-key", "organization-id", this._httpClient));

        return builder.Build();
    }

#pragma warning disable CA2000 // Dispose objects before losing scope
    private static List<HttpResponseMessage> GetTextWithToolCallResponses()
    {
        return
        [
            // First response: text + tool call
            new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StreamContent(File.OpenRead("TestData/aggregation_function_call_with_text_response.json"))
            },
            // Second response: final text only
            new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StreamContent(File.OpenRead("TestData/aggregation_final_response.json"))
            }
        ];
    }

    private static List<HttpResponseMessage> GetToolCallWithoutTextResponses()
    {
        return
        [
            // First response: tool call without text
            new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StreamContent(File.OpenRead("TestData/filters_multiple_function_calls_test_response.json"))
            },
            // Second response: final text only
            new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StreamContent(File.OpenRead("TestData/aggregation_final_response.json"))
            }
        ];
    }
#pragma warning restore CA2000

    private sealed class TerminatingFilter : IAutoFunctionInvocationFilter
    {
        public Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            context.Terminate = true;
            return Task.CompletedTask;
        }
    }

    #endregion
}

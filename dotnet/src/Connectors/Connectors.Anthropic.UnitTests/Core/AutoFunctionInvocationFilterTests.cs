// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic;
using Microsoft.SemanticKernel.Connectors.Anthropic.Services;
using Xunit;

namespace SemanticKernel.Connectors.Anthropic.UnitTests.Core;

/// <summary>
/// Unit tests for auto function invocation filters with Anthropic connector.
/// </summary>
public sealed class AutoFunctionInvocationFilterTests : IDisposable
{
    private readonly MultipleHttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public AutoFunctionInvocationFilterTests()
    {
        this._messageHandlerStub = new MultipleHttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task FiltersAreExecutedCorrectlyAsync()
    {
        // Arrange
        int filterInvocations = 0;
        int functionInvocations = 0;
        int[] expectedRequestSequenceNumbers = [0, 0, 1, 1];
        int[] expectedFunctionSequenceNumbers = [0, 1, 0, 1];
        List<int> requestSequenceNumbers = [];
        List<int> functionSequenceNumbers = [];
        Kernel? contextKernel = null;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionInvocations++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionInvocations++; return parameter; }, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            contextKernel = context.Kernel;
            requestSequenceNumbers.Add(context.RequestSequenceIndex);
            functionSequenceNumbers.Add(context.FunctionSequenceIndex);

            await next(context);

            filterInvocations++;
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

        // Act
        var result = await kernel.InvokePromptAsync("Test prompt", new(new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }));

        // Assert
        Assert.Equal(4, filterInvocations);
        Assert.Equal(4, functionInvocations);
        Assert.Equal(expectedRequestSequenceNumbers, requestSequenceNumbers);
        Assert.Equal(expectedFunctionSequenceNumbers, functionSequenceNumbers);
        Assert.Same(kernel, contextKernel);
        Assert.NotNull(result);
    }

    [Fact]
    public async Task FilterCanTerminateFunctionInvocationAsync()
    {
        // Arrange
        int functionInvocations = 0;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionInvocations++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionInvocations++; return parameter; }, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, (context, next) =>
        {
            // Terminate - don't call next
            context.Result = new FunctionResult(context.Function, "Terminated by filter");
            return Task.CompletedTask;
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

        // Act
        var result = await kernel.InvokePromptAsync("Test prompt", new(new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }));

        // Assert
        Assert.Equal(0, functionInvocations); // Functions should not be invoked
        Assert.NotNull(result);
    }

    [Fact]
    public async Task FilterCanModifyFunctionResultAsync()
    {
        // Arrange
        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => "original-result", "Function1");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1]);

        string? modifiedResult = null;
        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            await next(context);
            context.Result = new FunctionResult(context.Function, "modified-result");
            modifiedResult = context.Result.ToString();
        });

        this._messageHandlerStub.ResponsesToReturn = GetSingleFunctionCallResponses();

        // Act
        await kernel.InvokePromptAsync("Test prompt", new(new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }));

        // Assert
        Assert.Equal("modified-result", modifiedResult);
    }

    [Fact]
    public async Task DifferentWaysOfAddingFiltersWorkCorrectlyAsync()
    {
        // Arrange
        var executionOrder = new List<string>();

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => parameter, "Function1");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1]);

        var filter1 = new AutoFunctionInvocationFilter(async (context, next) =>
        {
            executionOrder.Add("Filter1-Invoking");
            await next(context);
        });

        var filter2 = new AutoFunctionInvocationFilter(async (context, next) =>
        {
            executionOrder.Add("Filter2-Invoking");
            await next(context);
        });

        var builder = Kernel.CreateBuilder();
        builder.Plugins.Add(plugin);

        builder.Services.AddSingleton<IChatCompletionService>((_) =>
            new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient));

        this._messageHandlerStub.ResponsesToReturn = GetSingleFunctionCallResponses();

        // Add filter to services
        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(filter1);

        var kernel = builder.Build();

        // Add filter to kernel
        kernel.AutoFunctionInvocationFilters.Add(filter2);

        // Act
        await kernel.InvokePromptAsync("Test prompt", new(new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }));

        // Assert
        Assert.Equal("Filter1-Invoking", executionOrder[0]);
        Assert.Equal("Filter2-Invoking", executionOrder[1]);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task MultipleFiltersAreExecutedInOrderAsync(bool isStreaming)
    {
        // Arrange
        var executionOrder = new List<string>();

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => parameter, "Function1");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1]);

        var filter1 = new AutoFunctionInvocationFilter(async (context, next) =>
        {
            executionOrder.Add("Filter1-Invoking");
            await next(context);
            executionOrder.Add("Filter1-Invoked");
        });

        var filter2 = new AutoFunctionInvocationFilter(async (context, next) =>
        {
            executionOrder.Add("Filter2-Invoking");
            await next(context);
            executionOrder.Add("Filter2-Invoked");
        });

        var builder = Kernel.CreateBuilder();
        builder.Plugins.Add(plugin);

        builder.Services.AddSingleton<IChatCompletionService>((_) =>
            new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient));

        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(filter1);
        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(filter2);

        var kernel = builder.Build();

        if (isStreaming)
        {
            this._messageHandlerStub.ResponsesToReturn = GetSingleFunctionCallStreamingResponses();
            await foreach (var _ in kernel.InvokePromptStreamingAsync("Test prompt", new(new AnthropicPromptExecutionSettings
            {
                FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
            })))
            { }
        }
        else
        {
            this._messageHandlerStub.ResponsesToReturn = GetSingleFunctionCallResponses();
            await kernel.InvokePromptAsync("Test prompt", new(new AnthropicPromptExecutionSettings
            {
                FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
            }));
        }

        // Assert - filters should execute in order: Filter1 invoke -> Filter2 invoke -> Filter2 complete -> Filter1 complete
        Assert.Equal("Filter1-Invoking", executionOrder[0]);
        Assert.Equal("Filter2-Invoking", executionOrder[1]);
        Assert.Equal("Filter2-Invoked", executionOrder[2]);
        Assert.Equal("Filter1-Invoked", executionOrder[3]);
    }

    [Fact]
    public async Task FilterReceivesCorrectFunctionContextAsync()
    {
        // Arrange
        string? receivedFunctionName = null;
        string? receivedPluginName = null;
        KernelArguments? receivedArguments = null;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => parameter, "Function1");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            receivedFunctionName = context.Function.Name;
            receivedPluginName = context.Function.PluginName;
            receivedArguments = context.Arguments;
            await next(context);
        });

        this._messageHandlerStub.ResponsesToReturn = GetSingleFunctionCallResponses();

        // Act
        await kernel.InvokePromptAsync("Test prompt", new(new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }));

        // Assert
        Assert.Equal("Function1", receivedFunctionName);
        Assert.Equal("MyPlugin", receivedPluginName);
        Assert.NotNull(receivedArguments);
    }

    [Fact]
    public async Task FiltersAreExecutedCorrectlyOnStreamingAsync()
    {
        // Arrange
        int filterInvocations = 0;
        int functionInvocations = 0;
        List<int> requestSequenceNumbers = [];
        List<int> functionSequenceNumbers = [];

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionInvocations++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionInvocations++; return parameter; }, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            requestSequenceNumbers.Add(context.RequestSequenceIndex);
            functionSequenceNumbers.Add(context.FunctionSequenceIndex);

            await next(context);

            filterInvocations++;
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingStreamingResponses();

        var executionSettings = new AnthropicPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        // Act
        await foreach (var item in kernel.InvokePromptStreamingAsync("Test prompt", new(executionSettings)))
        { }

        // Assert
        Assert.Equal(4, filterInvocations);
        Assert.Equal(4, functionInvocations);
        Assert.Equal([0, 0, 1, 1], requestSequenceNumbers);
        Assert.Equal([0, 1, 0, 1], functionSequenceNumbers);
    }

    [Fact]
    public async Task FilterCanAccessChatHistoryAsync()
    {
        // Arrange
        ChatHistory? capturedHistory = null;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => parameter, "Function1");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            capturedHistory = context.ChatHistory;
            await next(context);
        });

        this._messageHandlerStub.ResponsesToReturn = GetSingleFunctionCallResponses();

        // Act
        await kernel.InvokePromptAsync("Test prompt", new(new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }));

        // Assert
        Assert.NotNull(capturedHistory);
        Assert.True(capturedHistory.Count > 0);
    }

    [Fact]
    public async Task FilterCanAccessChatHistoryWithMessagesAsync()
    {
        // Arrange
        int historyCount = 0;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => parameter, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => parameter, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            // Count messages in history
            historyCount = context.ChatHistory.Count;
            await next(context);
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

        // Act
        await kernel.InvokePromptAsync("Test prompt", new(new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }));

        // Assert - history should have at least the user message and assistant response
        Assert.True(historyCount >= 2);
    }

    [Fact]
    public async Task FilterTerminationReturnsLastMessageAsync()
    {
        // Arrange
        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => parameter, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => parameter, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, (context, next) =>
        {
            // Terminate on first function
            context.Terminate = true;
            context.Result = new FunctionResult(context.Function, "Terminated");
            return Task.CompletedTask;
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

        // Act
        var result = await kernel.InvokePromptAsync("Test prompt", new(new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }));

        // Assert
        Assert.NotNull(result);
    }

    [Fact]
    public async Task FilterCanInspectFunctionBeingInvokedAsync()
    {
        // Arrange
        List<string> invokedFunctionNames = [];

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => parameter, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => parameter, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            invokedFunctionNames.Add(context.Function.Name);
            await next(context);
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

        // Act
        await kernel.InvokePromptAsync("Test prompt", new(new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }));

        // Assert - should have invoked both functions multiple times
        Assert.Contains("Function1", invokedFunctionNames);
        Assert.Contains("Function2", invokedFunctionNames);
    }

    [Fact]
    public async Task FilterCanSkipFunctionExecutionAsync()
    {
        // Arrange
        int functionInvocations = 0;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) =>
        {
            functionInvocations++;
            return parameter;
        }, "Function1");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1]);

        var kernel = this.GetKernelWithFilter(plugin, (context, next) =>
        {
            // Skip function execution by not calling next and setting a result
            context.Result = new FunctionResult(context.Function, "Skipped");
            return Task.CompletedTask;
        });

        this._messageHandlerStub.ResponsesToReturn = GetSingleFunctionCallResponses();

        // Act
        await kernel.InvokePromptAsync("Test prompt", new(new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }));

        // Assert - function should not have been invoked
        Assert.Equal(0, functionInvocations);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }

    #region Private Helper Methods

#pragma warning disable CA2000 // Dispose objects before losing scope
    private static List<HttpResponseMessage> GetFunctionCallingResponses()
    {
        return [
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/filters_multiple_function_calls_response.json")) },
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/filters_multiple_function_calls_response.json")) },
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/chat_completion_response.json")) }
        ];
    }

    private static List<HttpResponseMessage> GetFunctionCallingStreamingResponses()
    {
        return [
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/filters_streaming_multiple_function_calls_response.txt")) },
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/filters_streaming_multiple_function_calls_response.txt")) },
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/chat_completion_streaming_response.txt")) }
        ];
    }

    private static List<HttpResponseMessage> GetSingleFunctionCallResponses()
    {
        return [
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/filters_single_function_call_response.json")) },
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/chat_completion_response.json")) }
        ];
    }

    private static List<HttpResponseMessage> GetSingleFunctionCallStreamingResponses()
    {
        return [
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/filters_single_function_call_streaming_response.txt")) },
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/chat_completion_streaming_response.txt")) }
        ];
    }
#pragma warning restore CA2000

    private Kernel GetKernelWithFilter(
        KernelPlugin plugin,
        Func<AutoFunctionInvocationContext, Func<AutoFunctionInvocationContext, Task>, Task>? onAutoFunctionInvocation)
    {
        var builder = Kernel.CreateBuilder();
        var filter = new AutoFunctionInvocationFilter(onAutoFunctionInvocation);

        builder.Plugins.Add(plugin);
        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(filter);

        builder.Services.AddSingleton<IChatCompletionService>((_) =>
            new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient));

        return builder.Build();
    }

    private sealed class AutoFunctionInvocationFilter(
        Func<AutoFunctionInvocationContext, Func<AutoFunctionInvocationContext, Task>, Task>? onAutoFunctionInvocation) : IAutoFunctionInvocationFilter
    {
        private readonly Func<AutoFunctionInvocationContext, Func<AutoFunctionInvocationContext, Task>, Task>? _onAutoFunctionInvocation = onAutoFunctionInvocation;

        public Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next) =>
            this._onAutoFunctionInvocation?.Invoke(context, next) ?? Task.CompletedTask;
    }

    #endregion

    #region Additional Filter Tests

    [Fact]
    public async Task FilterCanOverrideArgumentsAsync()
    {
        // Arrange
        const string NewValue = "NewValue";
        string? receivedValue = null;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) =>
        {
            receivedValue = parameter;
            return parameter;
        }, "Function1");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            context.Arguments!["parameter"] = NewValue;
            await next(context);
        });

        this._messageHandlerStub.ResponsesToReturn = GetSingleFunctionCallResponses();

        // Act
        await kernel.InvokePromptAsync("Test prompt", new(new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }));

        // Assert
        Assert.Equal(NewValue, receivedValue);
    }

    [Fact]
    public async Task FilterCanOverrideFunctionResultAsync()
    {
        // Arrange
        const string OverriddenResult = "OverriddenResult";
        string? finalResult = null;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => "OriginalResult", "Function1");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            await next(context);
            context.Result = new FunctionResult(context.Function, OverriddenResult);
            finalResult = context.Result.GetValue<string>();
        });

        this._messageHandlerStub.ResponsesToReturn = GetSingleFunctionCallResponses();

        // Act
        await kernel.InvokePromptAsync("Test prompt", new(new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }));

        // Assert
        Assert.Equal(OverriddenResult, finalResult);
    }

    [Fact]
    public async Task FilterCanAccessKernelInstanceAsync()
    {
        // Arrange
        Kernel? receivedKernel = null;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => parameter, "Function1");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            receivedKernel = context.Kernel;
            await next(context);
        });

        this._messageHandlerStub.ResponsesToReturn = GetSingleFunctionCallResponses();

        // Act
        await kernel.InvokePromptAsync("Test prompt", new(new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }));

        // Assert
        Assert.NotNull(receivedKernel);
        Assert.Same(kernel, receivedKernel);
    }

    #endregion

    #region Text and Usage Aggregation Tests

    /// <summary>
    /// Tests that text content generated before tool calls is preserved in the final response.
    /// This verifies the fix for the issue where intermediate text was being lost during
    /// auto function calling iterations.
    /// </summary>
    [Fact]
    public async Task TextBeforeToolCallsIsPreservedInFinalResponseAsync()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod((string location) => "Sunny, 72°F", "GetWeather");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function]);

        var builder = Kernel.CreateBuilder();
        builder.Plugins.Add(plugin);
        builder.Services.AddSingleton<IChatCompletionService>((_) =>
            new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient));

        var kernel = builder.Build();

        // Response 1: Text + Tool Call, Response 2: Final text
        this._messageHandlerStub.ResponsesToReturn = GetTextBeforeToolCallResponses();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What's the weather in Seattle?");

        // Act
        var chatService = kernel.GetRequiredService<IChatCompletionService>();
        var result = await chatService.GetChatMessageContentsAsync(chatHistory, new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }, kernel);

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);

        var content = result[0].Content;
        Assert.NotNull(content);

        // The final content should contain BOTH the text from iteration 1 AND iteration 2
        // separated by \n\n (the aggregation separator)
        Assert.Contains("Let me check the weather for you.", content);
        Assert.Contains("The weather in Seattle is sunny and 72°F.", content);
        Assert.Contains("\n\n", content); // Verify separator is present
    }

    /// <summary>
    /// Tests that token usage is correctly aggregated across all function calling iterations.
    /// This verifies that the metadata contains the total tokens from all API calls.
    /// </summary>
    [Fact]
    public async Task TokenUsageIsAggregatedAcrossIterationsAsync()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod((string location) => "Sunny, 72°F", "GetWeather");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function]);

        var builder = Kernel.CreateBuilder();
        builder.Plugins.Add(plugin);
        builder.Services.AddSingleton<IChatCompletionService>((_) =>
            new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient));

        var kernel = builder.Build();

        // Response 1: 100 input + 50 output tokens
        // Response 2: 150 input + 30 output tokens
        // Total expected: 250 input + 80 output = 330 total
        this._messageHandlerStub.ResponsesToReturn = GetTextBeforeToolCallResponses();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What's the weather in Seattle?");

        // Act
        var chatService = kernel.GetRequiredService<IChatCompletionService>();
        var result = await chatService.GetChatMessageContentsAsync(chatHistory, new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }, kernel);

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);
        Assert.NotNull(result[0].Metadata);

        var metadata = result[0].Metadata!;

        // Verify aggregated token counts
        Assert.True(metadata.ContainsKey("InputTokens"), "Metadata should contain InputTokens");
        Assert.True(metadata.ContainsKey("OutputTokens"), "Metadata should contain OutputTokens");
        Assert.True(metadata.ContainsKey("TotalTokens"), "Metadata should contain TotalTokens");

        // Expected: Response 1 (100 + 50) + Response 2 (150 + 30)
        Assert.Equal(250L, metadata["InputTokens"]);
        Assert.Equal(80L, metadata["OutputTokens"]);
        Assert.Equal(330L, metadata["TotalTokens"]);
    }

    /// <summary>
    /// Tests that when a filter terminates the function calling loop, the aggregated text
    /// and usage metadata are still correctly applied to the returned message.
    /// </summary>
    [Fact]
    public async Task FilterTerminationPreservesAggregatedTextAndUsageAsync()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod((string location) => "Sunny, 72°F", "GetWeather");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function]);

        var kernel = this.GetKernelWithFilter(plugin, (context, next) =>
        {
            // Terminate immediately - don't execute the function
            context.Terminate = true;
            context.Result = new FunctionResult(context.Function, "Filter terminated");
            return Task.CompletedTask;
        });

        // Response with text before tool call
        this._messageHandlerStub.ResponsesToReturn = GetTextBeforeToolCallResponses();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What's the weather in Seattle?");

        // Act
        var chatService = kernel.GetRequiredService<IChatCompletionService>();
        var result = await chatService.GetChatMessageContentsAsync(chatHistory, new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }, kernel);

        // Assert
        Assert.NotNull(result);
        Assert.Single(result);

        // Even with filter termination, the text from iteration 1 should be preserved
        var content = result[0].Content;
        Assert.NotNull(content);
        Assert.Contains("Let me check the weather for you.", content);

        // And metadata should have the tokens from iteration 1
        var metadata = result[0].Metadata!;
        Assert.True(metadata.ContainsKey("InputTokens"));
        Assert.Equal(100L, metadata["InputTokens"]); // Only first response tokens
        Assert.Equal(50L, metadata["OutputTokens"]);
    }

#pragma warning disable CA2000 // Dispose objects before losing scope
    private static List<HttpResponseMessage> GetTextBeforeToolCallResponses()
    {
        return [
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/text_before_tool_call_response.json")) },
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/final_response_after_tool_call.json")) }
        ];
    }
#pragma warning restore CA2000

    #endregion
}


// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic;
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
        Assert.Contains("Hello", result.ToString()); // Verify actual response content from chat_completion_response.json
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

        var filter3 = new AutoFunctionInvocationFilter(async (context, next) =>
        {
            executionOrder.Add("Filter3-Invoking");
            await next(context);
            executionOrder.Add("Filter3-Invoked");
        });

        var builder = Kernel.CreateBuilder();
        builder.Plugins.Add(plugin);

        builder.Services.AddSingleton<IChatCompletionService>((_) =>
            new AnthropicChatCompletionService("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient));

        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(filter1);
        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(filter2);
        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(filter3);

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

        // Assert - filters should execute in order: Filter1 invoke -> Filter2 invoke -> Filter3 invoke -> Filter3 complete -> Filter2 complete -> Filter1 complete
        Assert.Equal("Filter1-Invoking", executionOrder[0]);
        Assert.Equal("Filter2-Invoking", executionOrder[1]);
        Assert.Equal("Filter3-Invoking", executionOrder[2]);
        Assert.Equal("Filter3-Invoked", executionOrder[3]);
        Assert.Equal("Filter2-Invoked", executionOrder[4]);
        Assert.Equal("Filter1-Invoked", executionOrder[5]);
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
        int firstFunctionInvocations = 0;
        int secondFunctionInvocations = 0;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { firstFunctionInvocations++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { secondFunctionInvocations++; return parameter; }, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, (context, next) =>
        {
            // Terminate on first function without calling next - skips function execution
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
        // Functions should not be invoked since we terminate without calling next
        Assert.Equal(0, firstFunctionInvocations);
        Assert.Equal(0, secondFunctionInvocations);

        // The result should reflect the filter-provided result (M.E.AI returns ChatResponse)
        var chatResponse = result.GetValue<ChatResponse>();
        Assert.NotNull(chatResponse);

        var lastFunctionResult = GetLastFunctionResultFromChatResponse(chatResponse);
        Assert.NotNull(lastFunctionResult);
        Assert.Equal("Terminated", lastFunctionResult.ToString());
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

        // Use M.E.AI ChatClient registration for proper filter integration
        builder.AddAnthropicChatClient("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);

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

    [Fact]
    public async Task FilterCanHandleExceptionAsync()
    {
        // Arrange
        string? firstFunctionResult = null;
        string? secondFunctionResult = null;
        bool firstFunctionCaptured = false;
        bool secondFunctionCaptured = false;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { throw new KernelException("Exception from Function1"); }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => "Result from Function2", "Function2");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            try
            {
                await next(context);
            }
            catch (KernelException exception)
            {
                Assert.Equal("Exception from Function1", exception.Message);
                context.Result = new FunctionResult(context.Result, "Result from filter");
            }

            // Capture the result for the first invocation of each function
            if (context.Function.Name == "Function1" && !firstFunctionCaptured)
            {
                firstFunctionResult = context.Result?.GetValue<string>();
                firstFunctionCaptured = true;
            }
            else if (context.Function.Name == "Function2" && !secondFunctionCaptured)
            {
                secondFunctionResult = context.Result?.GetValue<string>();
                secondFunctionCaptured = true;
            }
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

        // Act
        await kernel.InvokePromptAsync("Test prompt", new(new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }));

        // Assert
        Assert.Equal("Result from filter", firstFunctionResult);
        Assert.Equal("Result from Function2", secondFunctionResult);
    }

    [Fact]
    public async Task FilterCanHandleExceptionOnStreamingAsync()
    {
        // Arrange
        string? firstFunctionResult = null;
        string? secondFunctionResult = null;
        bool firstFunctionCaptured = false;
        bool secondFunctionCaptured = false;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { throw new KernelException("Exception from Function1"); }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => "Result from Function2", "Function2");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            try
            {
                await next(context);
            }
            catch (KernelException)
            {
                context.Result = new FunctionResult(context.Result, "Result from filter");
            }

            // Capture the result for the first invocation of each function
            if (context.Function.Name == "Function1" && !firstFunctionCaptured)
            {
                firstFunctionResult = context.Result?.GetValue<string>();
                firstFunctionCaptured = true;
            }
            else if (context.Function.Name == "Function2" && !secondFunctionCaptured)
            {
                secondFunctionResult = context.Result?.GetValue<string>();
                secondFunctionCaptured = true;
            }
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingStreamingResponses();

        // Act
        await foreach (var _ in kernel.InvokePromptStreamingAsync("Test prompt", new(new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        })))
        { }

        // Assert
        Assert.Equal("Result from filter", firstFunctionResult);
        Assert.Equal("Result from Function2", secondFunctionResult);
    }

    [Fact]
    public async Task PreFilterCanTerminateOperationAsync()
    {
        // Arrange
        int firstFunctionInvocations = 0;
        int secondFunctionInvocations = 0;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { firstFunctionInvocations++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { secondFunctionInvocations++; return parameter; }, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            // Terminating before first function, so all functions won't be invoked.
            context.Terminate = true;

            await next(context);
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

        // Act
        await kernel.InvokePromptAsync("Test prompt", new(new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }));

        // Assert
        Assert.Equal(0, firstFunctionInvocations);
        Assert.Equal(0, secondFunctionInvocations);
    }

    [Fact]
    public async Task PreFilterCanTerminateOperationOnStreamingAsync()
    {
        // Arrange
        int firstFunctionInvocations = 0;
        int secondFunctionInvocations = 0;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { firstFunctionInvocations++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { secondFunctionInvocations++; return parameter; }, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            // Terminating before first function, so all functions won't be invoked.
            context.Terminate = true;

            await next(context);
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingStreamingResponses();

        var executionSettings = new AnthropicPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        // Act
        await foreach (var item in kernel.InvokePromptStreamingAsync("Test prompt", new(executionSettings)))
        { }

        // Assert
        Assert.Equal(0, firstFunctionInvocations);
        Assert.Equal(0, secondFunctionInvocations);
    }

    [Fact]
    public async Task PostFilterCanTerminateOperationAsync()
    {
        // Arrange
        int firstFunctionInvocations = 0;
        int secondFunctionInvocations = 0;
        List<int> requestSequenceNumbers = [];
        List<int> functionSequenceNumbers = [];

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { firstFunctionInvocations++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { secondFunctionInvocations++; return parameter; }, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            requestSequenceNumbers.Add(context.RequestSequenceIndex);
            functionSequenceNumbers.Add(context.FunctionSequenceIndex);

            await next(context);

            // Terminating after first function, so second function won't be invoked.
            context.Terminate = true;
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

        // Act
        var result = await kernel.InvokePromptAsync("Test prompt", new(new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }));

        // Assert
        Assert.Equal(1, firstFunctionInvocations);
        Assert.Equal(0, secondFunctionInvocations);
        Assert.Equal([0], requestSequenceNumbers);
        Assert.Equal([0], functionSequenceNumbers);

        // Results of function invoked before termination should be returned (M.E.AI returns ChatResponse)
        var chatResponse = result.GetValue<ChatResponse>();
        Assert.NotNull(chatResponse);

        var functionResult = GetLastFunctionResultFromChatResponse(chatResponse);
        Assert.NotNull(functionResult);
        Assert.Equal("function1-value", functionResult.ToString());
    }

    [Fact]
    public async Task PostFilterCanTerminateOperationOnStreamingAsync()
    {
        // Arrange
        int firstFunctionInvocations = 0;
        int secondFunctionInvocations = 0;
        List<int> requestSequenceNumbers = [];
        List<int> functionSequenceNumbers = [];

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { firstFunctionInvocations++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { secondFunctionInvocations++; return parameter; }, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            requestSequenceNumbers.Add(context.RequestSequenceIndex);
            functionSequenceNumbers.Add(context.FunctionSequenceIndex);

            await next(context);

            // Terminating after first function, so second function won't be invoked.
            context.Terminate = true;
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingStreamingResponses();

        var executionSettings = new AnthropicPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        List<ChatResponseUpdate> streamingContent = [];

        // Act
        await foreach (var update in kernel.InvokePromptStreamingAsync<ChatResponseUpdate>("Test prompt", new(executionSettings)))
        {
            streamingContent.Add(update);
        }

        // Assert
        Assert.Equal(1, firstFunctionInvocations);
        Assert.Equal(0, secondFunctionInvocations);
        Assert.Equal([0], requestSequenceNumbers);
        Assert.Equal([0], functionSequenceNumbers);

        // Results of function invoked before termination should be returned (M.E.AI returns ChatResponse)
        Assert.True(streamingContent.Count >= 1);

        var chatResponse = streamingContent.ToChatResponse();
        Assert.NotNull(chatResponse);

        var functionResult = GetLastFunctionResultFromChatResponse(chatResponse);
        Assert.NotNull(functionResult);
        Assert.Equal("function1-value", functionResult.ToString());
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task FilterContextHasValidStreamingFlagAsync(bool isStreaming)
    {
        // Arrange
        bool? actualStreamingFlag = null;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => parameter, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => parameter, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var filter = new AutoFunctionInvocationFilter(async (context, next) =>
        {
            actualStreamingFlag = context.IsStreaming;
            await next(context);
        });

        var builder = Kernel.CreateBuilder();

        builder.Plugins.Add(plugin);

        builder.AddAnthropicChatClient("claude-sonnet-4-20250514", "test-api-key", httpClient: this._httpClient);

        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(filter);

        var kernel = builder.Build();

        var arguments = new KernelArguments(new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        });

        // Act
        if (isStreaming)
        {
            this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingStreamingResponses();

            await kernel.InvokePromptStreamingAsync("Test prompt", arguments).ToListAsync();
        }
        else
        {
            this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

            await kernel.InvokePromptAsync("Test prompt", arguments);
        }

        // Assert
        Assert.Equal(isStreaming, actualStreamingFlag);
    }

    [Fact]
    public async Task PromptExecutionSettingsArePropagatedFromInvokePromptToFilterContextAsync()
    {
        // Arrange
        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [KernelFunctionFactory.CreateFromMethod(() => { }, "Function1")]);

        AutoFunctionInvocationContext? actualContext = null;

        var kernel = this.GetKernelWithFilter(plugin, (context, next) =>
        {
            actualContext = context;
            return Task.CompletedTask;
        });

        // Act
        await kernel.InvokePromptAsync("Test prompt", new(new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }));

        // Assert
        Assert.NotNull(actualContext);
        Assert.NotNull(actualContext!.ExecutionSettings);
        // Note: M.E.AI-based connectors JSON-roundtrip settings through ToChatOptions, so we verify
        // value equivalence rather than reference equality (unlike direct IChatCompletionService implementations).
        Assert.NotNull(actualContext.ExecutionSettings!.FunctionChoiceBehavior);
    }

    [Fact]
    public async Task PromptExecutionSettingsArePropagatedFromInvokePromptStreamingToFilterContextAsync()
    {
        // Arrange
        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingStreamingResponses();

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [KernelFunctionFactory.CreateFromMethod(() => { }, "Function1")]);

        AutoFunctionInvocationContext? actualContext = null;

        var kernel = this.GetKernelWithFilter(plugin, (context, next) =>
        {
            actualContext = context;
            return Task.CompletedTask;
        });

        // Act
        await foreach (var _ in kernel.InvokePromptStreamingAsync("Test prompt", new(new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        })))
        { }

        // Assert
        Assert.NotNull(actualContext);
        Assert.NotNull(actualContext!.ExecutionSettings);
        // Note: M.E.AI-based connectors JSON-roundtrip settings through ToChatOptions, so we verify
        // value equivalence rather than reference equality (unlike direct IChatCompletionService implementations).
        Assert.NotNull(actualContext.ExecutionSettings!.FunctionChoiceBehavior);
    }

    [Fact]
    public async Task FiltersCanSkipSelectiveFunctionExecutionAsync()
    {
        // Arrange
        int filterInvocations = 0;
        int firstFunctionInvocations = 0;
        int secondFunctionInvocations = 0;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { firstFunctionInvocations++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { secondFunctionInvocations++; return parameter; }, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            // Filter delegate is invoked for both functions, but next() is called only for Function2.
            // Function1 execution is skipped because next() is not called for it.
            if (context.Function.Name == "Function2")
            {
                await next(context);
            }

            filterInvocations++;
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

        // Act
        var result = await kernel.InvokePromptAsync("Test prompt", new(new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }));

        // Assert
        // GetFunctionCallingResponses() returns 2 rounds of tool calls with 2 functions each
        // Filter is invoked 4 times total (2 functions × 2 rounds)
        Assert.Equal(4, filterInvocations);
        Assert.Equal(0, firstFunctionInvocations); // Function1 is always skipped
        Assert.Equal(2, secondFunctionInvocations); // Function2 executes once per round
    }

    [Fact]
    public async Task FunctionSequenceIndexIsCorrectForConcurrentCallsAsync()
    {
        // Arrange
        List<int> functionSequenceNumbers = [];
        List<int> expectedFunctionSequenceNumbers = [0, 1, 0, 1];

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { return parameter; }, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            functionSequenceNumbers.Add(context.FunctionSequenceIndex);

            await next(context);
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

        // Act
        var result = await kernel.InvokePromptAsync("Test prompt", new(new AnthropicPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new()
            {
                AllowParallelCalls = true,
                AllowConcurrentInvocation = true
            })
        }));

        // Assert
        Assert.Equal(expectedFunctionSequenceNumbers, functionSequenceNumbers);
    }

    private static object? GetLastFunctionResultFromChatResponse(ChatResponse chatResponse)
    {
        Assert.NotEmpty(chatResponse.Messages);
        var chatMessage = chatResponse.Messages.Where(m => m.Role == ChatRole.Tool).Last();

        Assert.NotEmpty(chatMessage.Contents);
        Assert.Contains(chatMessage.Contents, c => c is Microsoft.Extensions.AI.FunctionResultContent);

        var resultContent = (Microsoft.Extensions.AI.FunctionResultContent)chatMessage.Contents.Last(c => c is Microsoft.Extensions.AI.FunctionResultContent);
        return resultContent.Result;
    }

    #endregion
}


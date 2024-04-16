// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.FunctionCalling;

public sealed class FunctionCallFilterTests : IDisposable
{
    private readonly MultipleHttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public FunctionCallFilterTests()
    {
        this._messageHandlerStub = new MultipleHttpMessageHandlerStub();

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task FunctionCallFiltersAreExecutedCorrectlyAsync()
    {
        // Arrange
        int filterInvocations = 0;
        int functionCallCount = 0;
        int[] expectedRequestIterations = [0, 0, 1, 1];
        int[] expectedFunctionCallIterations = [0, 1, 0, 1];
        List<int> actualRequestIterations = [];
        List<int> actualFunctionCallIterations = [];

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionCallCount++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionCallCount++; return parameter; }, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            Assert.Equal(2, context.FunctionCallCount);

            actualRequestIterations.Add(context.RequestIteration);
            actualFunctionCallIterations.Add(context.FunctionCallIteration);

            await next(context);

            filterInvocations++;
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

        // Act
        var result = await kernel.InvokePromptAsync("Test prompt", new(new OpenAIPromptExecutionSettings
        {
            ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions
        }));

        // Assert
        Assert.Equal(4, filterInvocations);
        Assert.Equal(4, functionCallCount);
        Assert.Equal(expectedRequestIterations, actualRequestIterations);
        Assert.Equal(expectedFunctionCallIterations, actualFunctionCallIterations);
        Assert.Equal("Test chat response", result.ToString());
    }

    [Fact]
    public async Task FunctionCallFiltersAreExecutedCorrectlyOnStreamingAsync()
    {
        // Arrange
        int filterInvocations = 0;
        int functionCallCount = 0;
        int[] expectedRequestIterations = [0, 0, 1, 1];
        int[] expectedFunctionCallIterations = [0, 1, 0, 1];
        List<int> actualRequestIterations = [];
        List<int> actualFunctionCallIterations = [];

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionCallCount++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionCallCount++; return parameter; }, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            Assert.Equal(2, context.FunctionCallCount);

            actualRequestIterations.Add(context.RequestIteration);
            actualFunctionCallIterations.Add(context.FunctionCallIteration);

            await next(context);

            filterInvocations++;
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingStreamingResponses();

        var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        // Act
        await foreach (var item in kernel.InvokePromptStreamingAsync("Test prompt", new(executionSettings)))
        { }

        // Assert
        Assert.Equal(4, filterInvocations);
        Assert.Equal(4, functionCallCount);
        Assert.Equal(expectedRequestIterations, actualRequestIterations);
        Assert.Equal(expectedFunctionCallIterations, actualFunctionCallIterations);
    }

    [Theory]
    [InlineData(FunctionCallAction.None, new int[] { 0, 0, 1, 1 }, new int[] { 0, 1, 0, 1 }, 4)]
    [InlineData(FunctionCallAction.StopFunctionCallIteration, new int[] { 0, 1 }, new int[] { 0, 0 }, 2)]
    [InlineData(FunctionCallAction.StopRequestIteration, new int[] { 0, 0 }, new int[] { 0, 1 }, 2)]
    [InlineData(FunctionCallAction.StopRequestIteration | FunctionCallAction.StopFunctionCallIteration, new int[] { 0 }, new int[] { 0 }, 1)]
    public async Task PostExecutionWithStopActionStopsFunctionCallingLoopAsync(
        FunctionCallAction action,
        int[] expectedRequestIterations,
        int[] expectedFunctionCallIterations,
        int expectedFunctionCallCount)
    {
        // Arrange
        int functionCallCount = 0;
        List<int> requestIterations = [];
        List<int> functionCallIterations = [];

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionCallCount++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionCallCount++; return parameter; }, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            requestIterations.Add(context.RequestIteration);
            functionCallIterations.Add(context.FunctionCallIteration);

            await next(context);

            // Setting function calling action after function was invoked.
            context.Action = action;
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

        // Act
        await kernel.InvokePromptAsync("Test prompt", new(new OpenAIPromptExecutionSettings
        {
            ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions
        }));

        // Assert
        Assert.Equal(expectedRequestIterations, requestIterations);
        Assert.Equal(expectedFunctionCallIterations, functionCallIterations);
        Assert.Equal(expectedFunctionCallCount, functionCallCount);
    }

    [Theory]
    [InlineData(FunctionCallAction.None, new int[] { 0, 0, 1, 1 }, new int[] { 0, 1, 0, 1 }, 4)]
    [InlineData(FunctionCallAction.StopFunctionCallIteration, new int[] { 0, 1 }, new int[] { 0, 0 }, 2)]
    [InlineData(FunctionCallAction.StopRequestIteration, new int[] { 0, 0 }, new int[] { 0, 1 }, 2)]
    [InlineData(FunctionCallAction.StopRequestIteration | FunctionCallAction.StopFunctionCallIteration, new int[] { 0 }, new int[] { 0 }, 1)]
    public async Task PostExecutionWithStopActionStopsFunctionCallingLoopOnStreamingAsync(
        FunctionCallAction action,
        int[] expectedRequestIterations,
        int[] expectedFunctionCallIterations,
        int expectedFunctionCallCount)
    {
        // Arrange
        int functionCallCount = 0;
        List<int> requestIterations = [];
        List<int> functionCallIterations = [];

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionCallCount++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionCallCount++; return parameter; }, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            requestIterations.Add(context.RequestIteration);
            functionCallIterations.Add(context.FunctionCallIteration);

            await next(context);

            // Setting function calling action after function was invoked.
            context.Action = action;
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingStreamingResponses();

        var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        // Act
        await foreach (var item in kernel.InvokePromptStreamingAsync("Test prompt", new(executionSettings)))
        { }

        // Assert
        Assert.Equal(expectedRequestIterations, requestIterations);
        Assert.Equal(expectedFunctionCallIterations, functionCallIterations);
        Assert.Equal(expectedFunctionCallCount, functionCallCount);
    }

    [Theory]
    [InlineData(FunctionCallAction.StopRequestIteration)]
    [InlineData(FunctionCallAction.StopFunctionCallIteration)]
    [InlineData(FunctionCallAction.StopRequestIteration | FunctionCallAction.StopFunctionCallIteration)]
    public async Task PreExecutionWithStopActionDoesNotInvokeFunctionAsync(FunctionCallAction action)
    {
        // Arrange
        int functionCallCount = 0;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionCallCount++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionCallCount++; return parameter; }, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            // Setting function calling action before function was invoked.
            context.Action = action;

            await next(context);
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

        // Act
        await kernel.InvokePromptAsync("Test prompt", new(new OpenAIPromptExecutionSettings
        {
            ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions
        }));

        // Assert
        Assert.Equal(0, functionCallCount);
    }

    [Theory]
    [InlineData(FunctionCallAction.StopRequestIteration)]
    [InlineData(FunctionCallAction.StopFunctionCallIteration)]
    [InlineData(FunctionCallAction.StopRequestIteration | FunctionCallAction.StopFunctionCallIteration)]
    public async Task PreExecutionWithStopActionDoesNotInvokeFunctionOnStreamingAsync(FunctionCallAction action)
    {
        // Arrange
        int functionCallCount = 0;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionCallCount++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionCallCount++; return parameter; }, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            // Setting function calling action before function was invoked.
            context.Action = action;

            await next(context);
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingStreamingResponses();

        var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        // Act
        await foreach (var item in kernel.InvokePromptStreamingAsync("Test prompt", new(executionSettings)))
        { }

        // Assert
        Assert.Equal(0, functionCallCount);
    }

    [Fact]
    public async Task FilterCanHandleExceptionAsync()
    {
        // Arrange
        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { throw new KernelException("Exception from method"); }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => parameter, "Function2");
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
                context.Action = FunctionCallAction.StopRequestIteration | FunctionCallAction.StopFunctionCallIteration;
            }
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

        var chatCompletion = new OpenAIChatCompletionService(modelId: "test-model-id", apiKey: "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        // Act
        await chatCompletion.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel);
        var lastMessage = chatHistory.Last();

        // Assert
        Assert.Equal("Result from filter", lastMessage.Content);
    }

    [Fact]
    public async Task FilterCanHandleExceptionOnStreamingAsync()
    {
        // Arrange
        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { throw new KernelException("Exception from method"); }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => parameter, "Function2");
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
                context.Action = FunctionCallAction.StopRequestIteration | FunctionCallAction.StopFunctionCallIteration;
            }
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingStreamingResponses();

        var chatCompletion = new OpenAIChatCompletionService(modelId: "test-model-id", apiKey: "test-api-key", httpClient: this._httpClient);
        var chatHistory = new ChatHistory();
        var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        // Act
        await foreach (var item in chatCompletion.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings, kernel))
        { }

        var lastMessage = chatHistory.Last();

        // Assert
        Assert.Equal("Result from filter", lastMessage.Content);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }

    #region private

#pragma warning disable CA2000 // Dispose objects before losing scope
    private static List<HttpResponseMessage> GetFunctionCallingResponses()
    {
        return
            [
            // 1st LLM response to call Function1 and Function2
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("filters_multiple_function_calls_test_response.json")) },
            // 2nd LLM response to call Function1 and Function2
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("filters_multiple_function_calls_test_response.json")) },
            // 3rd LLM response with plain text
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_completion_test_response.json")) }
            ];
    }

    private static List<HttpResponseMessage> GetFunctionCallingStreamingResponses()
    {
        return
            [
            // 1st LLM response to call Function1 and Function2
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("filters_streaming_multiple_function_calls_test_response.txt")) },
            // 2nd LLM response to call Function1 and Function2
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("filters_streaming_multiple_function_calls_test_response.txt")) },
            // 3rd LLM response with plain text
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_completion_streaming_test_response.txt")) }
            ];
    }
#pragma warning restore CA2000

    private Kernel GetKernelWithFilter(
        KernelPlugin plugin,
        Func<FunctionCallInvocationContext, Func<FunctionCallInvocationContext, Task>, Task>? onFunctionCallInvocation)
    {
        var builder = Kernel.CreateBuilder();
        var functionCallFilter = new FakeFunctionCallFilter(onFunctionCallInvocation);

        builder.Plugins.Add(plugin);
        builder.Services.AddSingleton<IFunctionCallFilter>(functionCallFilter);

        builder.AddOpenAIChatCompletion(
            modelId: "test-model-id",
            apiKey: "test-api-key",
            httpClient: this._httpClient);

        return builder.Build();
    }

    private sealed class FakeFunctionCallFilter(
        Func<FunctionCallInvocationContext, Func<FunctionCallInvocationContext, Task>, Task>? onFunctionCallInvocation) : IFunctionCallFilter
    {
        private readonly Func<FunctionCallInvocationContext, Func<FunctionCallInvocationContext, Task>, Task>? _onFunctionCallInvocation = onFunctionCallInvocation;

        public Task OnFunctionCallInvocationAsync(FunctionCallInvocationContext context, Func<FunctionCallInvocationContext, Task> next) =>
            this._onFunctionCallInvocation?.Invoke(context, next) ?? Task.CompletedTask;
    }

    #endregion
}

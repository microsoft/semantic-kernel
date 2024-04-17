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

            if (context.ChatHistory.Last() is OpenAIChatMessageContent content)
            {
                Assert.Equal(2, content.ToolCalls.Count);
            }

            requestSequenceNumbers.Add(context.RequestSequenceNumber);
            functionSequenceNumbers.Add(context.FunctionSequenceNumber);

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
        Assert.Equal(4, functionInvocations);
        Assert.Equal(expectedRequestSequenceNumbers, requestSequenceNumbers);
        Assert.Equal(expectedFunctionSequenceNumbers, functionSequenceNumbers);
        Assert.Same(kernel, contextKernel);
        Assert.Equal("Test chat response", result.ToString());
    }

    [Fact]
    public async Task FiltersCanSkipFunctionExecutionAsync()
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
            // Filter delegate is invoked only for second function, the first one should be skipped.
            if (context.Function.Name == "Function2")
            {
                await next(context);
            }

            filterInvocations++;
        });

        using var response1 = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("filters_multiple_function_calls_test_response.json")) };
        using var response2 = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_completion_test_response.json")) };

        this._messageHandlerStub.ResponsesToReturn = [response1, response2];

        // Act
        var result = await kernel.InvokePromptAsync("Test prompt", new(new OpenAIPromptExecutionSettings
        {
            ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions
        }));

        // Assert
        Assert.Equal(2, filterInvocations);
        Assert.Equal(0, firstFunctionInvocations);
        Assert.Equal(1, secondFunctionInvocations);
    }

    [Fact]
    public async Task FiltersAreExecutedCorrectlyOnStreamingAsync()
    {
        // Arrange
        int filterInvocations = 0;
        int functionInvocations = 0;
        int[] expectedRequestSequenceNumbers = [0, 0, 1, 1];
        int[] expectedFunctionSequenceNumbers = [0, 1, 0, 1];
        List<int> requestSequenceNumbers = [];
        List<int> functionSequenceNumbers = [];

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionInvocations++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionInvocations++; return parameter; }, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            if (context.ChatHistory.Last() is OpenAIChatMessageContent content)
            {
                Assert.Equal(2, content.ToolCalls.Count);
            }

            requestSequenceNumbers.Add(context.RequestSequenceNumber);
            functionSequenceNumbers.Add(context.FunctionSequenceNumber);

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
        Assert.Equal(4, functionInvocations);
        Assert.Equal(expectedRequestSequenceNumbers, requestSequenceNumbers);
        Assert.Equal(expectedFunctionSequenceNumbers, functionSequenceNumbers);
    }

    [Theory]
    [InlineData(AutoFunctionInvocationAction.None, new int[] { 0, 0, 1, 1 }, new int[] { 0, 1, 0, 1 }, 4)]
    [InlineData(AutoFunctionInvocationAction.StopFunctionCallIteration, new int[] { 0, 1 }, new int[] { 0, 0 }, 2)]
    [InlineData(AutoFunctionInvocationAction.StopRequestIteration, new int[] { 0, 0 }, new int[] { 0, 1 }, 2)]
    [InlineData(AutoFunctionInvocationAction.StopRequestIteration | AutoFunctionInvocationAction.StopFunctionCallIteration, new int[] { 0 }, new int[] { 0 }, 1)]
    public async Task PostExecutionWithStopActionStopsFunctionCallingLoopAsync(
        AutoFunctionInvocationAction action,
        int[] expectedRequestSequenceNumbers,
        int[] expectedFunctionSequenceNumbers,
        int expectedFunctionInvocations)
    {
        // Arrange
        int functionInvocations = 0;
        List<int> requestSequenceNumbers = [];
        List<int> functionSequenceNumbers = [];

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionInvocations++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionInvocations++; return parameter; }, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            requestSequenceNumbers.Add(context.RequestSequenceNumber);
            functionSequenceNumbers.Add(context.FunctionSequenceNumber);

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
        Assert.Equal(expectedRequestSequenceNumbers, requestSequenceNumbers);
        Assert.Equal(expectedFunctionSequenceNumbers, functionSequenceNumbers);
        Assert.Equal(expectedFunctionInvocations, functionInvocations);
    }

    [Theory]
    [InlineData(AutoFunctionInvocationAction.None, new int[] { 0, 0, 1, 1 }, new int[] { 0, 1, 0, 1 }, 4)]
    [InlineData(AutoFunctionInvocationAction.StopFunctionCallIteration, new int[] { 0, 1 }, new int[] { 0, 0 }, 2)]
    [InlineData(AutoFunctionInvocationAction.StopRequestIteration, new int[] { 0, 0 }, new int[] { 0, 1 }, 2)]
    [InlineData(AutoFunctionInvocationAction.StopRequestIteration | AutoFunctionInvocationAction.StopFunctionCallIteration, new int[] { 0 }, new int[] { 0 }, 1)]
    public async Task PostExecutionWithStopActionStopsFunctionCallingLoopOnStreamingAsync(
        AutoFunctionInvocationAction action,
        int[] expectedRequestSequenceNumbers,
        int[] expectedFunctionSequenceNumbers,
        int expectedFunctionInvocations)
    {
        // Arrange
        int functionInvocations = 0;
        List<int> requestSequenceNumbers = [];
        List<int> functionSequenceNumbers = [];

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionInvocations++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionInvocations++; return parameter; }, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            requestSequenceNumbers.Add(context.RequestSequenceNumber);
            functionSequenceNumbers.Add(context.FunctionSequenceNumber);

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
        Assert.Equal(expectedRequestSequenceNumbers, requestSequenceNumbers);
        Assert.Equal(expectedFunctionSequenceNumbers, functionSequenceNumbers);
        Assert.Equal(expectedFunctionInvocations, functionInvocations);
    }

    [Theory]
    [InlineData(AutoFunctionInvocationAction.StopRequestIteration)]
    [InlineData(AutoFunctionInvocationAction.StopFunctionCallIteration)]
    [InlineData(AutoFunctionInvocationAction.StopRequestIteration | AutoFunctionInvocationAction.StopFunctionCallIteration)]
    public async Task PreExecutionWithStopActionDoesNotInvokeFunctionAsync(AutoFunctionInvocationAction action)
    {
        // Arrange
        int functionInvocations = 0;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionInvocations++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionInvocations++; return parameter; }, "Function2");

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
        Assert.Equal(0, functionInvocations);
    }

    [Theory]
    [InlineData(AutoFunctionInvocationAction.StopRequestIteration)]
    [InlineData(AutoFunctionInvocationAction.StopFunctionCallIteration)]
    [InlineData(AutoFunctionInvocationAction.StopRequestIteration | AutoFunctionInvocationAction.StopFunctionCallIteration)]
    public async Task PreExecutionWithStopActionDoesNotInvokeFunctionOnStreamingAsync(AutoFunctionInvocationAction action)
    {
        // Arrange
        int functionInvocations = 0;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionInvocations++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionInvocations++; return parameter; }, "Function2");

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
        Assert.Equal(0, functionInvocations);
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
                context.Action = AutoFunctionInvocationAction.StopRequestIteration | AutoFunctionInvocationAction.StopFunctionCallIteration;
            }
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

        var chatCompletion = new OpenAIChatCompletionService(modelId: "test-model-id", apiKey: "test-api-key", httpClient: this._httpClient);
        var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        // Act
        var result = await kernel.InvokePromptAsync("Test prompt", new(new OpenAIPromptExecutionSettings
        {
            ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions
        }));

        // Assert
        Assert.Equal("Result from filter", result.ToString());
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
                context.Action = AutoFunctionInvocationAction.StopRequestIteration | AutoFunctionInvocationAction.StopFunctionCallIteration;
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
        return [
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("filters_multiple_function_calls_test_response.json")) },
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("filters_multiple_function_calls_test_response.json")) },
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_completion_test_response.json")) }
        ];
    }

    private static List<HttpResponseMessage> GetFunctionCallingStreamingResponses()
    {
        return [
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("filters_streaming_multiple_function_calls_test_response.txt")) },
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("filters_streaming_multiple_function_calls_test_response.txt")) },
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(OpenAITestHelper.GetTestResponse("chat_completion_streaming_test_response.txt")) }
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

        builder.AddOpenAIChatCompletion(
            modelId: "test-model-id",
            apiKey: "test-api-key",
            httpClient: this._httpClient);

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
}

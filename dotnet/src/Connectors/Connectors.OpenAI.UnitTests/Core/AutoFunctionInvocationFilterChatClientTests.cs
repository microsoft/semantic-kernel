// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Core;

public sealed class AutoFunctionInvocationFilterChatClientTests : IDisposable
{
    private readonly MultipleHttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    public AutoFunctionInvocationFilterChatClientTests()
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

            requestSequenceNumbers.Add(context.RequestSequenceIndex);
            functionSequenceNumbers.Add(context.FunctionSequenceIndex);

            await next(context);

            filterInvocations++;
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

        // Act
        var result = await kernel.InvokePromptAsync("Test prompt", new(new OpenAIPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
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
        var result = await kernel.InvokePromptAsync("Test prompt", new(new OpenAIPromptExecutionSettings
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
            if (context.ChatHistory.Last() is OpenAIChatMessageContent content)
            {
                Assert.Equal(2, content.ToolCalls.Count);
            }

            requestSequenceNumbers.Add(context.RequestSequenceIndex);
            functionSequenceNumbers.Add(context.FunctionSequenceIndex);

            await next(context);

            filterInvocations++;
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingStreamingResponses();

        var executionSettings = new OpenAIPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

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
    public async Task DifferentWaysOfAddingFiltersWorkCorrectlyAsync()
    {
        // Arrange
        var executionOrder = new List<string>();

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => parameter, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => parameter, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

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

        builder.Services.AddOpenAIChatClient("model-id", "test-api-key", "organization-id", httpClient: this._httpClient);

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

        // Act

        // Case #1 - Add filter to services
        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(filter1);

        var kernel = builder.Build();

        // Case #2 - Add filter to kernel
        kernel.AutoFunctionInvocationFilters.Add(filter2);

        var result = await kernel.InvokePromptAsync("Test prompt", new(new PromptExecutionSettings
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
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => parameter, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

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

        builder.Services.AddOpenAIChatClient("model-id", "test-api-key", "organization-id", httpClient: this._httpClient);

        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(filter1);
        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(filter2);
        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(filter3);

        var kernel = builder.Build();

        var settings = new PromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        // Act
        if (isStreaming)
        {
            this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingStreamingResponses();

            await foreach (var item in kernel.InvokePromptStreamingAsync("Test prompt", new(settings)))
            { }
        }
        else
        {
            this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

            await kernel.InvokePromptAsync("Test prompt", new(settings));
        }

        // Assert
        Assert.Equal("Filter1-Invoking", executionOrder[0]);
        Assert.Equal("Filter2-Invoking", executionOrder[1]);
        Assert.Equal("Filter3-Invoking", executionOrder[2]);
        Assert.Equal("Filter3-Invoked", executionOrder[3]);
        Assert.Equal("Filter2-Invoked", executionOrder[4]);
        Assert.Equal("Filter1-Invoked", executionOrder[5]);
    }

    [Fact]
    public async Task FilterCanOverrideArgumentsAsync()
    {
        // Arrange
        const string NewValue = "NewValue";

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { return parameter; }, "Function2");

        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = this.GetKernelWithFilter(plugin, async (context, next) =>
        {
            context.Arguments!["parameter"] = NewValue;
            await next(context);
            context.Terminate = true;
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

        // Act
        var result = await kernel.InvokePromptAsync("Test prompt", new(new OpenAIPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }));

        // Assert
        var chatResponse = Assert.IsType<ChatResponse>(result.GetValue<ChatResponse>());
        Assert.NotNull(chatResponse);

        var lastFunctionResult = GetLastFunctionResultFromChatResponse(chatResponse);
        Assert.NotNull(lastFunctionResult);
        Assert.Equal("NewValue", lastFunctionResult.ToString());
    }

    [Fact]
    public async Task FilterCanHandleExceptionAsync()
    {
        // Arrange
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
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

        var chatClient = kernel.GetRequiredService<IChatClient>();

        var executionSettings = new PromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
        var options = executionSettings.ToChatOptions(kernel);
        List<ChatMessage> messageList = [new(ChatRole.System, "System message")];

        // Act
        var resultMessages = await chatClient.GetResponseAsync(messageList, options, CancellationToken.None);

        // Assert
        var firstToolMessage = resultMessages.Messages.First(m => m.Role == ChatRole.Tool);
        Assert.NotNull(firstToolMessage);
        var firstFunctionResult = firstToolMessage.Contents[^2] as Microsoft.Extensions.AI.FunctionResultContent;
        var secondFunctionResult = firstToolMessage.Contents[^1] as Microsoft.Extensions.AI.FunctionResultContent;

        Assert.NotNull(firstFunctionResult);
        Assert.NotNull(secondFunctionResult);
        Assert.Equal("Result from filter", firstFunctionResult.Result!.ToString());
        Assert.Equal("Result from Function2", secondFunctionResult.Result!.ToString());
    }

    [Fact]
    public async Task FilterCanHandleExceptionOnStreamingAsync()
    {
        // Arrange
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
        });

        this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingStreamingResponses();

        var chatClient = kernel.GetRequiredService<IChatClient>();

        var executionSettings = new PromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };
        var options = executionSettings.ToChatOptions(kernel);
        List<ChatMessage> messageList = [];

        // Act
        List<ChatResponseUpdate> streamingContent = [];
        await foreach (var update in chatClient.GetStreamingResponseAsync(messageList, options, CancellationToken.None))
        {
            streamingContent.Add(update);
        }
        var chatResponse = streamingContent.ToChatResponse();

        // Assert
        var firstToolMessage = chatResponse.Messages.First(m => m.Role == ChatRole.Tool);
        Assert.NotNull(firstToolMessage);
        var firstFunctionResult = firstToolMessage.Contents[^2] as Microsoft.Extensions.AI.FunctionResultContent;
        var secondFunctionResult = firstToolMessage.Contents[^1] as Microsoft.Extensions.AI.FunctionResultContent;

        Assert.NotNull(firstFunctionResult);
        Assert.NotNull(secondFunctionResult);
        Assert.Equal("Result from filter", firstFunctionResult.Result!.ToString());
        Assert.Equal("Result from Function2", secondFunctionResult.Result!.ToString());
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
            if (context.Function.Name == "Function2" && context.Function.PluginName == "MyPlugin")
            {
                await next(context);
            }

            filterInvocations++;
        });

        using var response1 = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(File.ReadAllText("TestData/filters_chatclient_multiple_function_calls_test_response.json")) };
        using var response2 = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(File.ReadAllText("TestData/chat_completion_test_response.json")) };

        this._messageHandlerStub.ResponsesToReturn = [response1, response2];

        // Act
        var result = await kernel.InvokePromptAsync("Test prompt", new(new PromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }));

        // Assert
        Assert.Equal(2, filterInvocations);
        Assert.Equal(0, firstFunctionInvocations);
        Assert.Equal(1, secondFunctionInvocations);
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
        await kernel.InvokePromptAsync("Test prompt", new(new PromptExecutionSettings
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

        var executionSettings = new PromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

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
        var functionResult = await kernel.InvokePromptAsync("Test prompt", new(new PromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        }));

        // Assert
        Assert.Equal(1, firstFunctionInvocations);
        Assert.Equal(0, secondFunctionInvocations);
        Assert.Equal([0], requestSequenceNumbers);
        Assert.Equal([0], functionSequenceNumbers);

        // Results of function invoked before termination should be returned
        var chatResponse = functionResult.GetValue<ChatResponse>();
        Assert.NotNull(chatResponse);

        var result = GetLastFunctionResultFromChatResponse(chatResponse);
        Assert.NotNull(result);
        Assert.Equal("function1-value", result.ToString());
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

        var executionSettings = new PromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

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

        // Results of function invoked before termination should be returned
        Assert.Equal(4, streamingContent.Count);

        var chatResponse = streamingContent.ToChatResponse();
        Assert.NotNull(chatResponse);

        var result = GetLastFunctionResultFromChatResponse(chatResponse);
        Assert.NotNull(result);
        Assert.Equal("function1-value", result.ToString());
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

        builder.Services.AddOpenAIChatClient("model-id", "test-api-key", "organization-id", httpClient: this._httpClient);

        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(filter);

        var kernel = builder.Build();

        var settings = new PromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        // Act
        if (isStreaming)
        {
            this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingStreamingResponses();

            await kernel.InvokePromptStreamingAsync("Test prompt", new(settings)).ToListAsync();
        }
        else
        {
            this._messageHandlerStub.ResponsesToReturn = GetFunctionCallingResponses();

            await kernel.InvokePromptAsync("Test prompt", new(settings));
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

        var expectedExecutionSettings = new PromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        // Act
        var result = await kernel.InvokePromptAsync("Test prompt", new(expectedExecutionSettings));

        // Assert
        Assert.NotNull(actualContext);
        Assert.Same(expectedExecutionSettings, actualContext!.ExecutionSettings);
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

        var expectedExecutionSettings = new PromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
        };

        // Act
        await foreach (var item in kernel.InvokePromptStreamingAsync("Test prompt", new(expectedExecutionSettings)))
        { }

        // Assert
        Assert.NotNull(actualContext);
        Assert.Same(expectedExecutionSettings, actualContext!.ExecutionSettings);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }

    #region private

    private static object? GetLastFunctionResultFromChatResponse(ChatResponse chatResponse)
    {
        Assert.NotEmpty(chatResponse.Messages);
        var chatMessage = chatResponse.Messages.Where(m => m.Role == ChatRole.Tool).Last();

        Assert.NotEmpty(chatMessage.Contents);
        Assert.Contains(chatMessage.Contents, c => c is Microsoft.Extensions.AI.FunctionResultContent);

        var resultContent = (Microsoft.Extensions.AI.FunctionResultContent)chatMessage.Contents.Last(c => c is Microsoft.Extensions.AI.FunctionResultContent);
        return resultContent.Result;
    }

#pragma warning disable CA2000 // Dispose objects before losing scope
    private static List<HttpResponseMessage> GetFunctionCallingResponses()
    {
        return [
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/filters_chatclient_multiple_function_calls_test_response.json")) },
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/filters_chatclient_multiple_function_calls_test_response.json")) },
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/chat_completion_test_response.json")) }
        ];
    }

    private static List<HttpResponseMessage> GetFunctionCallingStreamingResponses()
    {
        return [
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/filters_chatclient_streaming_multiple_function_calls_test_response.txt")) },
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/filters_chatclient_streaming_multiple_function_calls_test_response.txt")) },
            new HttpResponseMessage(HttpStatusCode.OK) { Content = new StreamContent(File.OpenRead("TestData/chat_completion_streaming_test_response.txt")) }
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

        builder.AddOpenAIChatClient("model-id", "test-api-key", "organization-id", httpClient: this._httpClient);

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

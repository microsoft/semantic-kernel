// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
#pragma warning disable IDE0005 // Using directive is unnecessary
using Microsoft.SemanticKernel.Connectors.FunctionCalling;

#pragma warning restore IDE0005 // Using directive is unnecessary
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Utilities.AIConnectors;

public class FunctionCallsProcessorTests
{
    private readonly FunctionCallsProcessor _sut = new();
    private readonly FunctionChoiceBehaviorOptions _functionChoiceBehaviorOptions = new();
    private readonly PromptExecutionSettings _promptExecutionSettings = new();

    [Fact]
    public void ItShouldReturnNoConfigurationIfNoBehaviorProvided()
    {
        // Act
        var config = this._sut.GetConfiguration(behavior: null, chatHistory: [], requestIndex: 0, kernel: null);

        // Assert
        Assert.Null(config);
    }

    [Fact]
    public void ItShouldNotDisableAutoInvocationIfMaximumAutoInvocationLimitNotReached()
    {
        // Act
        var config = this._sut.GetConfiguration(behavior: FunctionChoiceBehavior.Auto(), chatHistory: [], requestIndex: 127, kernel: CreateKernel());

        // Assert
        Assert.True(config!.AutoInvoke);
    }

    [Fact]
    public void ItShouldDisableAutoInvocationIfNoKernelIsProvided()
    {
        // Arrange
        var behaviorMock = new Mock<FunctionChoiceBehavior>();
        behaviorMock
            .Setup(b => b.GetConfiguration(It.IsAny<FunctionChoiceBehaviorConfigurationContext>()))
            .Returns(new FunctionChoiceBehaviorConfiguration(options: new FunctionChoiceBehaviorOptions()));

        // Act
        var config = this._sut.GetConfiguration(behavior: behaviorMock.Object, chatHistory: [], requestIndex: 128, kernel: null); // No kernel provided

        // Assert
        Assert.False(config!.AutoInvoke);
    }

    [Fact]
    public void ItShouldDisableAutoInvocationIfMaximumAutoInvocationLimitReached()
    {
        // Act
        var config = this._sut.GetConfiguration(behavior: FunctionChoiceBehavior.Auto(), chatHistory: [], requestIndex: 128, kernel: CreateKernel());

        // Assert
        Assert.False(config!.AutoInvoke);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItShouldDisableAutoInvocationIfMaximumInflightAutoInvocationLimitReachedAsync(bool invokeConcurrently)
    {
        // Arrange
        this._functionChoiceBehaviorOptions.AllowConcurrentInvocation = invokeConcurrently;

        var kernel = CreateKernel();

        var chatMessageContent = new ChatMessageContent();
        chatMessageContent.Items.Add(new FunctionCallContent("ProcessFunctionCallsRecursivelyToReachInflightLimitAsync", "test"));

        int invocationNumber = 0;
        FunctionChoiceBehaviorConfiguration? expectedConfiguration = null;

        async Task ProcessFunctionCallsRecursivelyToReachInflightLimitAsync()
        {
            if (invocationNumber++ == 128) // 128 is the current Inflight limit
            {
                expectedConfiguration = this._sut.GetConfiguration(behavior: FunctionChoiceBehavior.Auto(), chatHistory: [], requestIndex: 0, kernel: kernel);
                return;
            }

            await this._sut.ProcessFunctionCallsAsync(
                chatMessageContent: chatMessageContent,
                executionSettings: this._promptExecutionSettings,
                chatHistory: [],
                requestIndex: 0,
                checkIfFunctionAdvertised: (_) => true,
                options: this._functionChoiceBehaviorOptions,
                kernel: kernel,
                isStreaming: false,
                cancellationToken: CancellationToken.None);
        }

        kernel.Plugins.AddFromFunctions("test", [KernelFunctionFactory.CreateFromMethod(ProcessFunctionCallsRecursivelyToReachInflightLimitAsync, "ProcessFunctionCallsRecursivelyToReachInflightLimitAsync")]);

        // Act
        var res = await kernel.InvokeAsync("test", "ProcessFunctionCallsRecursivelyToReachInflightLimitAsync");

        // Assert
        Assert.NotNull(expectedConfiguration);
        Assert.False(expectedConfiguration!.AutoInvoke);
    }

    [Fact]
    public async Task ItShouldAddFunctionCallAssistantMessageToChatHistoryAsync()
    {
        // Arrange
        var chatHistory = new ChatHistory();
        var chatMessageContent = new ChatMessageContent();

        // Act
        await this._sut.ProcessFunctionCallsAsync(
                chatMessageContent: chatMessageContent,
                executionSettings: this._promptExecutionSettings,
                chatHistory: chatHistory,
                requestIndex: 0,
                checkIfFunctionAdvertised: (_) => true,
                options: this._functionChoiceBehaviorOptions,
                kernel: CreateKernel(),
                isStreaming: false,
                cancellationToken: CancellationToken.None);

        // Assert
        Assert.Single(chatHistory);
        Assert.Contains(chatMessageContent, chatHistory);
    }

    [Fact]
    public async Task ItShouldAddFunctionCallExceptionToChatHistoryAsync()
    {
        // Arrange
        var chatHistory = new ChatHistory();

        var chatMessageContent = new ChatMessageContent();
        chatMessageContent.Items.Add(new FunctionCallContent("Function1", "MyPlugin")
        {
            Exception = new JsonException("Deserialization failed.") // Simulate an exception
        });

        // Act
        await this._sut.ProcessFunctionCallsAsync(
                chatMessageContent: chatMessageContent,
                executionSettings: this._promptExecutionSettings,
                chatHistory: chatHistory,
                requestIndex: 0,
                checkIfFunctionAdvertised: (_) => true,
                options: this._functionChoiceBehaviorOptions,
                kernel: CreateKernel(),
                isStreaming: false,
                cancellationToken: CancellationToken.None);

        // Assert
        var functionResult = chatHistory[1].Items.OfType<FunctionResultContent>().Single();

        Assert.Equal("MyPlugin", functionResult.PluginName);
        Assert.Equal("Function1", functionResult.FunctionName);
        Assert.Equal("Error: Function call processing failed. Correct yourself. Deserialization failed.", functionResult.Result);
    }

    [Fact]
    public async Task ItShouldAddFunctionInvocationExceptionToChatHistoryAsync()
    {
        // Arrange
        var function1 = KernelFunctionFactory.CreateFromMethod(() => { throw new InvalidOperationException("This is test exception."); }, "Function1");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1]);

        var kernel = CreateKernel(plugin);

        var chatHistory = new ChatHistory();

        var chatMessageContent = new ChatMessageContent();
        chatMessageContent.Items.Add(new FunctionCallContent("Function1", "MyPlugin"));

        // Act
        await this._sut.ProcessFunctionCallsAsync(
                chatMessageContent: chatMessageContent,
                executionSettings: this._promptExecutionSettings,
                chatHistory: chatHistory,
                requestIndex: 0,
                checkIfFunctionAdvertised: (_) => true,
                options: this._functionChoiceBehaviorOptions,
                kernel: kernel,
                isStreaming: false,
                cancellationToken: CancellationToken.None);

        // Assert
        var functionResult = chatHistory[1].Items.OfType<FunctionResultContent>().Single();

        Assert.Equal("MyPlugin", functionResult.PluginName);
        Assert.Equal("Function1", functionResult.FunctionName);
        Assert.Equal("Error: Exception while invoking function. This is test exception.", functionResult.Result);
    }

    [Fact]
    public async Task ItShouldAddErrorToChatHistoryIfFunctionCallNotAdvertisedAsync()
    {
        // Arrange
        var chatHistory = new ChatHistory();

        var chatMessageContent = new ChatMessageContent();
        chatMessageContent.Items.Add(new FunctionCallContent("Function1", "MyPlugin"));

        // Act
        await this._sut.ProcessFunctionCallsAsync(
                chatMessageContent: chatMessageContent,
                executionSettings: this._promptExecutionSettings,
                chatHistory: chatHistory,
                requestIndex: 0,
                checkIfFunctionAdvertised: (_) => false, // Return false to simulate that the function is not advertised
                options: this._functionChoiceBehaviorOptions,
                kernel: CreateKernel(),
                isStreaming: false,
                cancellationToken: CancellationToken.None);

        // Assert
        var functionResult = chatHistory[1].Items.OfType<FunctionResultContent>().Single();

        Assert.Equal("MyPlugin", functionResult.PluginName);
        Assert.Equal("Function1", functionResult.FunctionName);
        Assert.Equal("Error: Function call request for a function that wasn't defined. Correct yourself.", functionResult.Result);
    }

    [Fact]
    public async Task ItShouldAddErrorToChatHistoryIfFunctionIsNotRegisteredOnKernelAsync()
    {
        // Arrange
        var chatHistory = new ChatHistory();

        var chatMessageContent = new ChatMessageContent();
        chatMessageContent.Items.Add(new FunctionCallContent("Function1", "MyPlugin")); // The call for function that is not registered on the kernel

        // Act
        await this._sut.ProcessFunctionCallsAsync(
                chatMessageContent: chatMessageContent,
                executionSettings: this._promptExecutionSettings,
                chatHistory: chatHistory,
                requestIndex: 0,
                checkIfFunctionAdvertised: (_) => true,
                options: this._functionChoiceBehaviorOptions,
                kernel: CreateKernel(),
                isStreaming: false,
                cancellationToken: CancellationToken.None);

        // Assert
        var functionResult = chatHistory[1].Items.OfType<FunctionResultContent>().Single();

        Assert.Equal("MyPlugin", functionResult.PluginName);
        Assert.Equal("Function1", functionResult.FunctionName);
        Assert.Equal("Error: Requested function could not be found. Correct yourself.", functionResult.Result);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItShouldInvokeFunctionsAsync(bool invokeConcurrently)
    {
        // Arrange
        this._functionChoiceBehaviorOptions.AllowConcurrentInvocation = invokeConcurrently;

        int functionInvocations = 0;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { Interlocked.Increment(ref functionInvocations); return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { Interlocked.Increment(ref functionInvocations); return parameter; }, "Function2");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = CreateKernel(plugin);

        var chatHistory = new ChatHistory();

        var chatMessageContent = new ChatMessageContent();
        chatMessageContent.Items.Add(new FunctionCallContent("Function1", "MyPlugin", arguments: new KernelArguments() { ["parameter"] = "function1-result" }));
        chatMessageContent.Items.Add(new FunctionCallContent("Function2", "MyPlugin", arguments: new KernelArguments() { ["parameter"] = "function2-result" }));

        // Act
        await this._sut.ProcessFunctionCallsAsync(
                chatMessageContent: chatMessageContent,
                executionSettings: this._promptExecutionSettings,
                chatHistory: chatHistory,
                requestIndex: 0,
                checkIfFunctionAdvertised: (_) => true,
                options: this._functionChoiceBehaviorOptions,
                kernel: kernel,
                isStreaming: false,
                cancellationToken: CancellationToken.None);

        // Assert
        Assert.Equal(2, functionInvocations);

        Assert.Equal(3, chatHistory.Count);

        var functionResults = chatHistory.SelectMany(x => x.Items).OfType<FunctionResultContent>().ToList();
        Assert.Equal(2, functionResults.Count);

        var function1Result = functionResults.Single(x => x.FunctionName == "Function1");
        Assert.Equal("MyPlugin", function1Result.PluginName);
        Assert.Equal("function1-result", function1Result.Result);

        var function2Result = functionResults.Single(x => x.FunctionName == "Function2");
        Assert.Equal("MyPlugin", function2Result.PluginName);
        Assert.Equal("function2-result", function2Result.Result);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItShouldInvokeFiltersAsync(bool invokeConcurrently)
    {
        // Arrange
        this._functionChoiceBehaviorOptions.AllowConcurrentInvocation = invokeConcurrently;

        int filterInvocations = 0;
        int functionInvocations = 0;
        int[] expectedRequestSequenceNumbers = [0, 0];
        int[] expectedFunctionSequenceNumbers = [0, 1];
        ConcurrentBag<int> requestSequenceNumbers = [];
        ConcurrentBag<int> functionSequenceNumbers = [];

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionInvocations++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { functionInvocations++; return parameter; }, "Function2");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        Kernel? kernel = null;
        kernel = CreateKernel(plugin, async (context, next) =>
        {
            Assert.Equal(kernel, context.Kernel);

            requestSequenceNumbers.Add(context.RequestSequenceIndex);
            functionSequenceNumbers.Add(context.FunctionSequenceIndex);

            await next(context);

            Interlocked.Increment(ref filterInvocations);
        });

        var chatMessageContent = new ChatMessageContent();
        chatMessageContent.Items.Add(new FunctionCallContent("Function1", "MyPlugin", arguments: new KernelArguments() { ["parameter"] = "function1-result" }));
        chatMessageContent.Items.Add(new FunctionCallContent("Function2", "MyPlugin", arguments: new KernelArguments() { ["parameter"] = "function2-result" }));

        var chatHistory = new ChatHistory();

        // Act
        await this._sut.ProcessFunctionCallsAsync(
                chatMessageContent: chatMessageContent,
                executionSettings: this._promptExecutionSettings,
                chatHistory: chatHistory,
                requestIndex: 0,
                checkIfFunctionAdvertised: (_) => true,
                options: this._functionChoiceBehaviorOptions,
                kernel: kernel!,
                isStreaming: false,
                cancellationToken: CancellationToken.None);

        // Assert
        Assert.Equal(2, filterInvocations);
        Assert.Equal(2, functionInvocations);

        Assert.Equal(3, chatHistory.Count);
        Assert.Same(chatMessageContent, chatHistory[0]);

        Assert.Equal(expectedRequestSequenceNumbers, requestSequenceNumbers);

        if (!invokeConcurrently)
        {
            Assert.Equal(expectedFunctionSequenceNumbers, functionSequenceNumbers.Reverse());
        }

        var functionResults = chatHistory.SelectMany(x => x.Items).OfType<FunctionResultContent>().ToList();
        Assert.Equal(2, functionResults.Count);

        var function1Result = functionResults.Single(x => x.FunctionName == "Function1");
        Assert.Equal("MyPlugin", function1Result.PluginName);
        Assert.Equal("function1-result", function1Result.Result);

        var function2Result = functionResults.Single(x => x.FunctionName == "Function2");
        Assert.Equal("MyPlugin", function2Result.PluginName);
        Assert.Equal("function2-result", function2Result.Result);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItShouldInvokeMultipleFiltersInOrderAsync(bool invokeConcurrently)
    {
        // Arrange
        this._functionChoiceBehaviorOptions.AllowConcurrentInvocation = invokeConcurrently;

        var function = KernelFunctionFactory.CreateFromMethod(() => "Result");
        var filterInvocationLog = new ConcurrentBag<string>();

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => parameter, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => parameter, "Function2");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var filter1 = new AutoFunctionInvocationFilter(async (context, next) =>
        {
            filterInvocationLog.Add("Filter1-Invoking");
            await next(context);
            filterInvocationLog.Add("Filter1-Invoked");
        });

        var filter2 = new AutoFunctionInvocationFilter(async (context, next) =>
        {
            filterInvocationLog.Add("Filter2-Invoking");
            await next(context);
            filterInvocationLog.Add("Filter2-Invoked");
        });

        var filter3 = new AutoFunctionInvocationFilter(async (context, next) =>
        {
            filterInvocationLog.Add("Filter3-Invoking");
            await next(context);
            filterInvocationLog.Add("Filter3-Invoked");
        });

        var builder = Kernel.CreateBuilder();

        builder.Plugins.Add(plugin);

        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(filter1);
        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(filter2);
        builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(filter3);

        var kernel = builder.Build();

        var chatMessageContent = new ChatMessageContent();
        chatMessageContent.Items.Add(new FunctionCallContent("Function1", "MyPlugin", arguments: new KernelArguments() { ["parameter"] = "function1-result" }));
        chatMessageContent.Items.Add(new FunctionCallContent("Function2", "MyPlugin", arguments: new KernelArguments() { ["parameter"] = "function2-result" }));

        var chatHistory = new ChatHistory();

        // Act
        await this._sut.ProcessFunctionCallsAsync(
                chatMessageContent: chatMessageContent,
                executionSettings: this._promptExecutionSettings,
                chatHistory: chatHistory,
                requestIndex: 0,
                checkIfFunctionAdvertised: (_) => true,
                options: this._functionChoiceBehaviorOptions,
                kernel: kernel!,
                isStreaming: false,
                cancellationToken: CancellationToken.None);

        // Assert
        string[] reversedLog = filterInvocationLog.Reverse().ToArray();
        Assert.Equal("Filter1-Invoking", reversedLog[0]);
        Assert.Equal("Filter2-Invoking", reversedLog[1]);
        Assert.Equal("Filter3-Invoking", reversedLog[2]);
        Assert.Equal("Filter3-Invoked", reversedLog[3]);
        Assert.Equal("Filter2-Invoked", reversedLog[4]);
        Assert.Equal("Filter1-Invoked", reversedLog[5]);
        Assert.Equal(3, chatHistory.Count);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task FilterCanOverrideArgumentsAsync(bool invokeConcurrently)
    {
        // Arrange
        this._functionChoiceBehaviorOptions.AllowConcurrentInvocation = invokeConcurrently;

        const string NewValue = "NewValue";

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { return parameter; }, "Function2");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = CreateKernel(plugin, async (context, next) =>
        {
            context.Arguments!["parameter"] = NewValue;
            await next(context);
        });

        var chatMessageContent = new ChatMessageContent();
        chatMessageContent.Items.Add(new FunctionCallContent("Function1", "MyPlugin", arguments: new KernelArguments() { ["parameter"] = "function1-result" }));
        chatMessageContent.Items.Add(new FunctionCallContent("Function2", "MyPlugin", arguments: new KernelArguments() { ["parameter"] = "function2-result" }));

        var chatHistory = new ChatHistory();

        // Act
        await this._sut.ProcessFunctionCallsAsync(
                chatMessageContent: chatMessageContent,
                executionSettings: this._promptExecutionSettings,
                chatHistory: chatHistory,
                requestIndex: 0,
                checkIfFunctionAdvertised: (_) => true,
                options: this._functionChoiceBehaviorOptions,
                kernel: kernel!,
                isStreaming: false,
                cancellationToken: CancellationToken.None);

        // Assert
        Assert.Equal(3, chatHistory.Count);
        Assert.Same(chatMessageContent, chatHistory[0]);
        var function1Result = chatHistory[1].Items.OfType<FunctionResultContent>().Single();
        Assert.Equal("NewValue", function1Result.Result);
        var function2Result = chatHistory[2].Items.OfType<FunctionResultContent>().Single();
        Assert.Equal("NewValue", function2Result.Result);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task FilterCanHandleExceptionAsync(bool invokeConcurrently)
    {
        // Arrange
        this._functionChoiceBehaviorOptions.AllowConcurrentInvocation = invokeConcurrently;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { throw new KernelException("Exception from Function1"); }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => "Result from Function2", "Function2");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = CreateKernel(plugin, async (context, next) =>
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

        var chatMessageContent = new ChatMessageContent();
        chatMessageContent.Items.Add(new FunctionCallContent("Function1", "MyPlugin", arguments: new KernelArguments() { ["parameter"] = "function1-result" }));
        chatMessageContent.Items.Add(new FunctionCallContent("Function2", "MyPlugin", arguments: new KernelArguments() { ["parameter"] = "function2-result" }));

        var chatHistory = new ChatHistory();
        chatHistory.AddSystemMessage("System message");

        // Act
        await this._sut.ProcessFunctionCallsAsync(
                chatMessageContent: chatMessageContent,
                executionSettings: this._promptExecutionSettings,
                chatHistory: chatHistory,
                requestIndex: 0,
                checkIfFunctionAdvertised: (_) => true,
                options: this._functionChoiceBehaviorOptions,
                kernel: kernel!,
                isStreaming: false,
                cancellationToken: CancellationToken.None);

        var firstFunctionResult = chatHistory[^2].Content;
        var secondFunctionResult = chatHistory[^1].Content;

        // Assert
        Assert.Equal("Result from filter", firstFunctionResult);
        Assert.Equal("Result from Function2", secondFunctionResult);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task FiltersCanSkipFunctionExecutionAsync(bool invokeConcurrently)
    {
        // Arrange
        this._functionChoiceBehaviorOptions.AllowConcurrentInvocation = invokeConcurrently;

        int filterInvocations = 0;
        int firstFunctionInvocations = 0;
        int secondFunctionInvocations = 0;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { firstFunctionInvocations++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { secondFunctionInvocations++; return parameter; }, "Function2");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = CreateKernel(plugin, async (context, next) =>
        {
            // Filter delegate is invoked only for second function, the first one should be skipped.
            if (context.Function.Name == "Function2")
            {
                await next(context);
            }

            Interlocked.Increment(ref filterInvocations);
        });

        var chatMessageContent = new ChatMessageContent();
        chatMessageContent.Items.Add(new FunctionCallContent("Function1", "MyPlugin", arguments: new KernelArguments() { ["parameter"] = "function1-result" }));
        chatMessageContent.Items.Add(new FunctionCallContent("Function2", "MyPlugin", arguments: new KernelArguments() { ["parameter"] = "function2-result" }));

        var chatHistory = new ChatHistory();

        // Act
        await this._sut.ProcessFunctionCallsAsync(
                chatMessageContent: chatMessageContent,
                executionSettings: this._promptExecutionSettings,
                chatHistory: chatHistory,
                requestIndex: 0,
                checkIfFunctionAdvertised: (_) => true,
                options: this._functionChoiceBehaviorOptions,
                kernel: kernel!,
                isStreaming: false,
                cancellationToken: CancellationToken.None);

        // Assert
        Assert.Equal(2, filterInvocations);
        Assert.Equal(0, firstFunctionInvocations);
        Assert.Equal(1, secondFunctionInvocations);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task PreFilterCanTerminateOperationAsync(bool invokeConcurrently)
    {
        // Arrange
        this._functionChoiceBehaviorOptions.AllowConcurrentInvocation = invokeConcurrently;

        int firstFunctionInvocations = 0;
        int secondFunctionInvocations = 0;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { firstFunctionInvocations++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { secondFunctionInvocations++; return parameter; }, "Function2");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = CreateKernel(plugin, async (context, next) =>
        {
            // Terminating before first function, so all functions won't be invoked.
            context.Terminate = true;

            await next(context);
        });

        var chatMessageContent = new ChatMessageContent();
        chatMessageContent.Items.Add(new FunctionCallContent("Function1", "MyPlugin", arguments: new KernelArguments() { ["parameter"] = "function1-result" }));
        chatMessageContent.Items.Add(new FunctionCallContent("Function2", "MyPlugin", arguments: new KernelArguments() { ["parameter"] = "function2-result" }));

        var chatHistory = new ChatHistory();

        // Act
        await this._sut.ProcessFunctionCallsAsync(
                chatMessageContent: chatMessageContent,
                executionSettings: this._promptExecutionSettings,
                chatHistory: chatHistory,
                requestIndex: 0,
                checkIfFunctionAdvertised: (_) => true,
                options: this._functionChoiceBehaviorOptions,
                kernel: kernel!,
                isStreaming: false,
                cancellationToken: CancellationToken.None);

        // Assert
        Assert.Equal(0, firstFunctionInvocations);
        Assert.Equal(0, secondFunctionInvocations);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task PostFilterCanTerminateOperationAsync(bool invokeConcurrently)
    {
        // Arrange
        this._functionChoiceBehaviorOptions.AllowConcurrentInvocation = invokeConcurrently;

        int firstFunctionInvocations = 0;
        int secondFunctionInvocations = 0;

        var function1 = KernelFunctionFactory.CreateFromMethod((string parameter) => { firstFunctionInvocations++; return parameter; }, "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod((string parameter) => { secondFunctionInvocations++; return parameter; }, "Function2");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1, function2]);

        var kernel = CreateKernel(plugin, async (context, next) =>
        {
            await next(context);

            context.Terminate = true;
        });

        var chatMessageContent = new ChatMessageContent();
        chatMessageContent.Items.Add(new FunctionCallContent("Function1", "MyPlugin", arguments: new KernelArguments() { ["parameter"] = "function1-result" }));
        chatMessageContent.Items.Add(new FunctionCallContent("Function2", "MyPlugin", arguments: new KernelArguments() { ["parameter"] = "function2-result" }));

        var chatHistory = new ChatHistory();

        // Act
        await this._sut.ProcessFunctionCallsAsync(
                chatMessageContent: chatMessageContent,
                executionSettings: this._promptExecutionSettings,
                chatHistory: chatHistory,
                requestIndex: 0,
                checkIfFunctionAdvertised: (_) => true,
                options: this._functionChoiceBehaviorOptions,
                kernel: kernel!,
                isStreaming: false,
                cancellationToken: CancellationToken.None);

        // Assert
        if (invokeConcurrently)
        {
            Assert.Equal(3, chatHistory.Count); // Result of all functions should be added to chat history

            var functionResults = chatHistory.SelectMany(x => x.Items).OfType<FunctionResultContent>().ToList();
            Assert.Equal(2, functionResults.Count);

            Assert.Contains(functionResults, x => x.FunctionName == "Function1" && x.Result?.ToString() == "function1-result");
            Assert.Contains(functionResults, x => x.FunctionName == "Function2" && x.Result?.ToString() == "function2-result");

            Assert.Equal(1, firstFunctionInvocations);
            Assert.Equal(1, secondFunctionInvocations);
        }
        else
        {
            Assert.Equal(2, chatHistory.Count); // Result of only first function should be added to chat history

            var functionResults = chatHistory.SelectMany(x => x.Items).OfType<FunctionResultContent>().ToList();
            var functionResult = Assert.Single(functionResults);

            Assert.Equal("Function1", functionResult.FunctionName);
            Assert.Equal("function1-result", functionResult.Result);

            Assert.Equal(1, firstFunctionInvocations);
            Assert.Equal(0, secondFunctionInvocations);
        }
    }

    [Fact]
    public async Task ItShouldHandleChatMessageContentAsFunctionResultAsync()
    {
        // Arrange
        var function1 = KernelFunctionFactory.CreateFromMethod(() => { return new ChatMessageContent(AuthorRole.User, "function1-result"); }, "Function1");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1]);

        var kernel = CreateKernel(plugin);

        var chatHistory = new ChatHistory();

        var chatMessageContent = new ChatMessageContent();
        chatMessageContent.Items.Add(new FunctionCallContent("Function1", "MyPlugin"));

        // Act
        await this._sut.ProcessFunctionCallsAsync(
                chatMessageContent: chatMessageContent,
                executionSettings: this._promptExecutionSettings,
                chatHistory: chatHistory,
                requestIndex: 0,
                checkIfFunctionAdvertised: (_) => true,
                options: this._functionChoiceBehaviorOptions,
                kernel: kernel,
                isStreaming: false,
                cancellationToken: CancellationToken.None);

        // Assert
        Assert.Equal(2, chatHistory.Count);

        var function1Result = chatHistory[1].Items.OfType<FunctionResultContent>().Single();
        Assert.Equal("MyPlugin", function1Result.PluginName);
        Assert.Equal("Function1", function1Result.FunctionName);
        Assert.IsType<string>(function1Result.Result);
        Assert.Equal("function1-result", function1Result.Result);
    }

    [Fact]
    public async Task ItShouldSerializeFunctionResultOfUnknownTypeAsync()
    {
        // Arrange
        var function1 = KernelFunctionFactory.CreateFromMethod(() => { return new { a = 2, b = "test" }; }, "Function1");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function1]);

        var kernel = CreateKernel(plugin);

        var chatHistory = new ChatHistory();

        var chatMessageContent = new ChatMessageContent();
        chatMessageContent.Items.Add(new FunctionCallContent("Function1", "MyPlugin"));

        // Act
        await this._sut.ProcessFunctionCallsAsync(
                chatMessageContent: chatMessageContent,
                executionSettings: this._promptExecutionSettings,
                chatHistory: chatHistory,
                requestIndex: 0,
                checkIfFunctionAdvertised: (_) => true,
                options: this._functionChoiceBehaviorOptions,
                kernel: kernel,
                isStreaming: false,
                cancellationToken: CancellationToken.None);

        // Assert
        Assert.Equal(2, chatHistory.Count);

        var function1Result = chatHistory[1].Items.OfType<FunctionResultContent>().Single();
        Assert.Equal("MyPlugin", function1Result.PluginName);
        Assert.Equal("Function1", function1Result.FunctionName);
        Assert.IsType<string>(function1Result.Result);
        Assert.Equal("{\"a\":2,\"b\":\"test\"}", function1Result.Result);
    }

    [Fact]
    public void ItShouldHandleFunctionResultsOfStringType()
    {
        // Arrange
        string functionResult = "Test result";

        // Act
        var result = FunctionCallsProcessor.ProcessFunctionResult(functionResult);

        // Assert
        Assert.Equal(functionResult, result);
    }

    [Fact]
    public void ItShouldHandleFunctionResultsOfChatMessageContentType()
    {
        // Arrange
        var functionResult = new ChatMessageContent(AuthorRole.User, "Test result");

        // Act
        var result = FunctionCallsProcessor.ProcessFunctionResult(functionResult);

        // Assert
        Assert.Equal("Test result", result);
    }

    [Fact]
    public void ItShouldSerializeFunctionResultsOfComplexType()
    {
        // Arrange
        var functionResult = new { a = 2, b = "test" };

        // Act
        var result = FunctionCallsProcessor.ProcessFunctionResult(functionResult);

        // Assert
        Assert.Equal("{\"a\":2,\"b\":\"test\"}", result);
    }

    [Fact]
    public void ItShouldSerializeFunctionResultsWithStringProperties()
    {
        // Arrange
        var functionResult = new { Text = "ﾃｽﾄ" };

        // Act
        var result = FunctionCallsProcessor.ProcessFunctionResult(functionResult);

        // Assert
        Assert.Equal("{\"Text\":\"ﾃｽﾄ\"}", result);
    }

    [Fact]
    public async Task ItShouldPassPromptExecutionSettingsToAutoFunctionInvocationFilterAsync()
    {
        // Arrange
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [KernelFunctionFactory.CreateFromMethod(() => { }, "Function1")]);

        AutoFunctionInvocationContext? actualContext = null;

        Kernel kernel = CreateKernel(plugin, (context, next) =>
        {
            actualContext = context;
            return Task.CompletedTask;
        });

        var chatMessageContent = new ChatMessageContent();
        chatMessageContent.Items.Add(new FunctionCallContent("Function1", "MyPlugin", arguments: new KernelArguments() { ["parameter"] = "function1-result" }));

        // Act
        await this._sut.ProcessFunctionCallsAsync(
                chatMessageContent: chatMessageContent,
                executionSettings: this._promptExecutionSettings,
                chatHistory: new ChatHistory(),
                requestIndex: 0,
                checkIfFunctionAdvertised: (_) => true,
                options: this._functionChoiceBehaviorOptions,
                kernel: kernel!,
                isStreaming: false,
                cancellationToken: CancellationToken.None);

        // Assert
        Assert.NotNull(actualContext);
        Assert.Same(this._promptExecutionSettings, actualContext!.ExecutionSettings);
    }

    private sealed class AutoFunctionInvocationFilter(
        Func<AutoFunctionInvocationContext, Func<AutoFunctionInvocationContext, Task>, Task>? onAutoFunctionInvocation) : IAutoFunctionInvocationFilter
    {
        private readonly Func<AutoFunctionInvocationContext, Func<AutoFunctionInvocationContext, Task>, Task>? _onAutoFunctionInvocation = onAutoFunctionInvocation;

        public Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next) =>
            this._onAutoFunctionInvocation?.Invoke(context, next) ?? Task.CompletedTask;
    }

    private static Kernel CreateKernel(KernelPlugin? plugin = null, Func<AutoFunctionInvocationContext, Func<AutoFunctionInvocationContext, Task>, Task>? onAutoFunctionInvocation = null)
    {
        var builder = Kernel.CreateBuilder();

        if (plugin is not null)
        {
            builder.Plugins.Add(plugin);
        }

        if (onAutoFunctionInvocation is not null)
        {
            builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(new AutoFunctionInvocationFilter(onAutoFunctionInvocation));
        }

        return builder.Build();
    }
}

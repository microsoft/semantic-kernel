// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextGeneration;
using Microsoft.SemanticKernel.Events;
using Moq;
using Xunit;

// ReSharper disable StringLiteralTypo

namespace SemanticKernel.UnitTests;

public class KernelTests
{
    [Fact]
    public void ItProvidesAccessToFunctionsViaFunctionCollection()
    {
        // Arrange
        var factory = new Mock<Func<IServiceProvider, ITextGenerationService>>();
        var kernel = new KernelBuilder().WithServices(c =>
        {
            c.AddSingleton<ITextGenerationService>(factory.Object);
        }).Build();

        kernel.ImportPluginFromObject<MyPlugin>("mySk");

        // Act & Assert - 3 functions, var name is not case sensitive
        Assert.NotNull(kernel.Plugins.GetFunction("mySk", "sayhello"));
        Assert.NotNull(kernel.Plugins.GetFunction("MYSK", "SayHello"));
        Assert.NotNull(kernel.Plugins.GetFunction("mySk", "ReadFunctionCollectionAsync"));
        Assert.NotNull(kernel.Plugins.GetFunction("MYSK", "ReadFunctionCollectionAsync"));
    }

    [Fact]
    public async Task InvokeAsyncDoesNotRunWhenCancelledAsync()
    {
        // Arrange
        var kernel = new Kernel();
        var functions = kernel.ImportPluginFromObject<MyPlugin>();

        using CancellationTokenSource cts = new();
        cts.Cancel();

        // Act
        await Assert.ThrowsAnyAsync<OperationCanceledException>(() => kernel.InvokeAsync(functions["GetAnyValue"], cancellationToken: cts.Token));
    }

    [Fact]
    public async Task InvokeAsyncRunsWhenNotCancelledAsync()
    {
        // Arrange
        var kernel = new Kernel();
        kernel.ImportPluginFromObject<MyPlugin>("mySk");

        using CancellationTokenSource cts = new();

        // Act
        var result = await kernel.InvokeAsync(kernel.Plugins.GetFunction("mySk", "GetAnyValue"), cancellationToken: cts.Token);

        // Assert
        Assert.False(string.IsNullOrEmpty(result.GetValue<string>()));
    }

    [Fact]
    public void ItImportsPluginsNotCaseSensitive()
    {
        // Act
        IKernelPlugin plugin = new Kernel().ImportPluginFromObject<MyPlugin>();

        // Assert
        Assert.Equal(3, plugin.Count());
        Assert.True(plugin.Contains("GetAnyValue"));
        Assert.True(plugin.Contains("getanyvalue"));
        Assert.True(plugin.Contains("GETANYVALUE"));
    }

    [Fact]
    public void ItAllowsToImportTheSamePluginMultipleTimes()
    {
        // Arrange
        var kernel = new Kernel();

        // Act - Assert no exception occurs
        kernel.ImportPluginFromObject<MyPlugin>();
        kernel.ImportPluginFromObject<MyPlugin>("plugin1");
        kernel.ImportPluginFromObject<MyPlugin>("plugin2");
        kernel.ImportPluginFromObject<MyPlugin>("plugin3");
    }

    [Fact]
    public async Task InvokeAsyncHandlesPreInvocationAsync()
    {
        // Arrange
        var kernel = new Kernel();
        int functionInvocations = 0;
        var function = KernelFunctionFactory.CreateFromMethod(() => functionInvocations++);

        var handlerInvocations = 0;
        kernel.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            handlerInvocations++;
        };

        // Act
        var result = await kernel.InvokeAsync(function);

        // Assert
        Assert.Equal(1, functionInvocations);
        Assert.Equal(1, handlerInvocations);
    }

    [Fact]
    public async Task RunStreamingAsyncHandlesPreInvocationAsync()
    {
        // Arrange
        var kernel = new Kernel();
        int functionInvocations = 0;
        var function = KernelFunctionFactory.CreateFromMethod(() => functionInvocations++);

        var handlerInvocations = 0;
        kernel.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            handlerInvocations++;
        };

        // Act
        await foreach (var chunk in kernel.InvokeStreamingAsync(function)) { }

        // Assert
        Assert.Equal(1, functionInvocations);
        Assert.Equal(1, handlerInvocations);
    }

    [Fact]
    public async Task RunStreamingAsyncHandlesPreInvocationWasCancelledAsync()
    {
        // Arrange
        var kernel = new Kernel();
        int functionInvocations = 0;
        var function = KernelFunctionFactory.CreateFromMethod(() => functionInvocations++);

        var handlerInvocations = 0;
        kernel.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            handlerInvocations++;
            e.Cancel = true;
        };

        // Act
        IAsyncEnumerable<StreamingContentBase> enumerable = kernel.InvokeStreamingAsync<StreamingContentBase>(function);
        IAsyncEnumerator<StreamingContentBase> enumerator = enumerable.GetAsyncEnumerator();
        var e = await Assert.ThrowsAsync<KernelFunctionCanceledException>(async () => await enumerator.MoveNextAsync());

        // Assert
        Assert.Equal(1, handlerInvocations);
        Assert.Equal(0, functionInvocations);
        Assert.Same(function, e.Function);
        Assert.Same(kernel, e.Kernel);
        Assert.Empty(e.Arguments);
    }

    [Fact]
    public async Task RunStreamingAsyncPreInvocationCancelationDontTriggerInvokedHandlerAsync()
    {
        // Arrange
        var kernel = new Kernel();
        var functions = kernel.ImportPluginFromObject<MyPlugin>();

        var invoked = 0;
        kernel.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            e.Cancel = true;
        };

        kernel.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            invoked++;
        };

        // Act
        IAsyncEnumerable<StreamingContentBase> enumerable = kernel.InvokeStreamingAsync<StreamingContentBase>(functions["GetAnyValue"]);
        IAsyncEnumerator<StreamingContentBase> enumerator = enumerable.GetAsyncEnumerator();
        var e = await Assert.ThrowsAsync<KernelFunctionCanceledException>(async () => await enumerator.MoveNextAsync());

        // Assert
        Assert.Equal(0, invoked);
    }

    [Fact]
    public async Task InvokeStreamingAsyncDoesNotHandlePostInvocationAsync()
    {
        // Arrange
        var kernel = new Kernel();
        int functionInvocations = 0;
        var function = KernelFunctionFactory.CreateFromMethod(() => functionInvocations++);

        int handlerInvocations = 0;
        kernel.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            handlerInvocations++;
        };

        // Act
        await foreach (var chunk in kernel.InvokeStreamingAsync(function))
        {
        }

        // Assert
        Assert.Equal(1, functionInvocations);
        Assert.Equal(0, handlerInvocations);
    }

    [Fact]
    public async Task InvokeAsyncHandlesPreInvocationWasCancelledAsync()
    {
        // Arrange
        var kernel = new Kernel();
        int functionInvocations = 0;
        var function = KernelFunctionFactory.CreateFromMethod(() => functionInvocations++);

        var handlerInvocations = 0;
        kernel.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            handlerInvocations++;
            e.Cancel = true;
        };

        // Act
        KernelFunctionCanceledException ex = await Assert.ThrowsAsync<KernelFunctionCanceledException>(() => kernel.InvokeAsync(function));

        // Assert
        Assert.Equal(1, handlerInvocations);
        Assert.Equal(0, functionInvocations);
        Assert.Same(function, ex.Function);
        Assert.Null(ex.FunctionResult);
    }

    [Fact]
    public async Task InvokeAsyncHandlesPreInvocationCancelationDontRunSubsequentFunctionsInThePipelineAsync()
    {
        // Arrange
        var kernel = new Kernel();
        int functionInvocations = 0;
        var function = KernelFunctionFactory.CreateFromMethod(() => functionInvocations++);

        int handlerInvocations = 0;
        kernel.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            handlerInvocations++;
            e.Cancel = true;
        };

        // Act
        KernelFunctionCanceledException ex = await Assert.ThrowsAsync<KernelFunctionCanceledException>(() => kernel.InvokeAsync(function));

        // Assert
        Assert.Equal(1, handlerInvocations);
        Assert.Equal(0, functionInvocations);
        Assert.Same(function, ex.Function);
        Assert.Null(ex.FunctionResult);
    }

    [Fact]
    public async Task InvokeAsyncPreInvocationCancelationDontTriggerInvokedHandlerAsync()
    {
        // Arrange
        var kernel = new Kernel();
        var functions = kernel.ImportPluginFromObject<MyPlugin>();

        var invoked = 0;
        kernel.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            e.Cancel = true;
        };

        kernel.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            invoked++;
        };

        // Act
        KernelFunctionCanceledException ex = await Assert.ThrowsAsync<KernelFunctionCanceledException>(() => kernel.InvokeAsync(functions["GetAnyValue"]));

        // Assert
        Assert.Equal(0, invoked);
        Assert.Same(functions["GetAnyValue"], ex.Function);
        Assert.Null(ex.FunctionResult);
    }

    [Fact]
    public async Task InvokeAsyncHandlesPostInvocationAsync()
    {
        // Arrange
        var kernel = new Kernel();
        int functionInvocations = 0;
        var function = KernelFunctionFactory.CreateFromMethod(() => functionInvocations++);

        int handlerInvocations = 0;
        kernel.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            handlerInvocations++;
        };

        // Act
        var result = await kernel.InvokeAsync(function);

        // Assert
        Assert.Equal(1, functionInvocations);
        Assert.Equal(1, handlerInvocations);
    }

    [Fact]
    public async Task InvokeAsyncHandlesPostInvocationWithServicesAsync()
    {
        // Arrange
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        var sut = new KernelBuilder().WithServices(c => c.AddSingleton<ITextGenerationService>(mockTextCompletion.Object)).Build();
        var function = KernelFunctionFactory.CreateFromPrompt("Write a simple phrase about UnitTests");

        var invoked = 0;

        sut.FunctionInvoked += (sender, e) =>
        {
            invoked++;
        };

        // Act
        var result = await sut.InvokeAsync(function);

        // Assert
        Assert.Equal(1, invoked);
        mockTextCompletion.Verify(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Exactly(1));
    }

    [Fact]
    public async Task InvokeAsyncHandlesPostInvocationAndCancellationExceptionContainsResultAsync()
    {
        // Arrange
        var kernel = new Kernel();
        object result = 42;
        var function = KernelFunctionFactory.CreateFromMethod(() => result);
        var args = new KernelArguments() { { "a", "b" } };

        kernel.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            e.Cancel = true;
        };

        // Act
        KernelFunctionCanceledException ex = await Assert.ThrowsAsync<KernelFunctionCanceledException>(() => kernel.InvokeAsync(function, args));

        // Assert
        Assert.Same(kernel, ex.Kernel);
        Assert.Same(function, ex.Function);
        Assert.Same(args, ex.Arguments);
        Assert.NotNull(ex.FunctionResult);
        Assert.Same(result, ex.FunctionResult.GetValue<object>());
    }

    [Fact]
    public async Task InvokeAsyncHandlesPostInvocationAndCancellationExceptionContainsModifiedResultAsync()
    {
        // Arrange
        var kernel = new Kernel();
        object result = 42;
        object newResult = 84;
        var function = KernelFunctionFactory.CreateFromMethod(() => result);
        var args = new KernelArguments() { { "a", "b" } };

        kernel.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            e.SetResultValue(newResult);
            e.Cancel = true;
        };

        // Act
        KernelFunctionCanceledException ex = await Assert.ThrowsAsync<KernelFunctionCanceledException>(() => kernel.InvokeAsync(function, args));

        // Assert
        Assert.Same(kernel, ex.Kernel);
        Assert.Same(function, ex.Function);
        Assert.Same(args, ex.Arguments);
        Assert.NotNull(ex.FunctionResult);
        Assert.Same(newResult, ex.FunctionResult.GetValue<object>());
    }

    [Fact]
    public async Task InvokeAsyncChangeVariableInvokingHandlerAsync()
    {
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod((string originalInput) => originalInput);

        var originalInput = "Importance";
        var newInput = "Problems";

        kernel.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            e.Arguments[KernelArguments.InputParameterName] = newInput;
        };

        // Act
        var result = await kernel.InvokeAsync(function, new(originalInput));

        // Assert
        Assert.Equal(newInput, result.GetValue<string>());
    }

    [Fact]
    public async Task InvokeAsyncChangeVariableInvokedHandlerAsync()
    {
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => { });

        var originalInput = "Importance";
        var newInput = "Problems";

        kernel.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            e.SetResultValue(newInput);
        };

        // Act
        var result = await kernel.InvokeAsync(function, new(originalInput));

        // Assert
        Assert.Equal(newInput, result.GetValue<string>());
    }

    [Fact]
    public async Task ItReturnsFunctionResultsCorrectlyAsync()
    {
        // Arrange
        var kernel = new Kernel();

        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "Function1");

        // Act
        var result = await kernel.InvokeAsync(function);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Result", result.GetValue<string>());
    }

    [Fact]
    public async Task ItReturnsChangedResultsFromFunctionInvokedEventsAsync()
    {
        var kernel = new Kernel();

        // Arrange
        var function1 = KernelFunctionFactory.CreateFromMethod(() => "Result1", "Function1");
        const string ExpectedValue = "new result";

        kernel.FunctionInvoked += (object? sender, FunctionInvokedEventArgs args) =>
        {
            args.SetResultValue(ExpectedValue);
        };

        // Act
        var result = await kernel.InvokeAsync(function1);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(ExpectedValue, result.GetValue<string>());
    }

    [Fact]
    public async Task ItReturnsChangedResultsFromFunctionInvokingEventsAsync()
    {
        // Arrange
        var kernel = new Kernel();

        var function1 = KernelFunctionFactory.CreateFromMethod((string injectedVariable) => injectedVariable, "Function1");
        const string ExpectedValue = "injected value";

        kernel.FunctionInvoking += (object? sender, FunctionInvokingEventArgs args) =>
        {
            args.Arguments["injectedVariable"] = ExpectedValue;
        };

        // Act
        var result = await kernel.InvokeAsync(function1);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(ExpectedValue, result.GetValue<string>());
    }

    [Fact]
    public async Task ItCanFindAndRunFunctionAsync()
    {
        //Arrange
        var serviceProvider = new Mock<IServiceProvider>();
        var serviceSelector = new Mock<IAIServiceSelector>();

        var function = KernelFunctionFactory.CreateFromMethod(() => "fake result", "function");

        var kernel = new Kernel(new Mock<IServiceProvider>().Object);
        kernel.Plugins.Add(new KernelPlugin("plugin", new[] { function }));

        //Act
        var result = await kernel.InvokeAsync("plugin", "function");

        //Assert
        Assert.NotNull(result);
        Assert.Equal("fake result", result.GetValue<string>());
    }

    [Fact]
    public void ItShouldBePossibleToSetAndGetCultureAssociatedWithKernel()
    {
        //Arrange
        var kernel = new Kernel();

        var culture = CultureInfo.GetCultureInfo(28);

        //Act
        kernel.Culture = culture;

        //Assert
        Assert.Equal(culture, kernel.Culture);
    }

    [Fact]
    public void ItDefaultsLoggerFactoryToNullLoggerFactory()
    {
        //Arrange
        var kernel = new Kernel();

        //Assert
        Assert.Same(NullLoggerFactory.Instance, kernel.LoggerFactory);
    }

    [Fact]
    public void ItDefaultsDataToEmptyDictionary()
    {
        //Arrange
        var kernel = new Kernel();

        //Assert
        Assert.Empty(kernel.Data);
    }

    [Fact]
    public void ItDefaultsPluginsToEmptyCollection()
    {
        //Arrange
        var kernel = new Kernel();

        //Assert
        Assert.Empty(kernel.Plugins);
    }

    [Fact]
    public void InvariantCultureShouldBeReturnedIfNoCultureWasAssociatedWithKernel()
    {
        //Arrange
        var kernel = new Kernel();

        //Act
        var culture = kernel.Culture;

        //Assert
        Assert.Same(CultureInfo.InvariantCulture, culture);
    }

    [Fact]
    public void ItDeepClonesAllRelevantStateInClone()
    {
        // Kernel with all properties set
        var serviceSelector = new Mock<IAIServiceSelector>();
        var loggerFactory = new Mock<ILoggerFactory>();
        var serviceProvider = new ServiceCollection()
            .AddSingleton(serviceSelector.Object)
#pragma warning disable CA2000 // Dispose objects before losing scope
            .AddSingleton(new HttpClient())
#pragma warning restore CA2000
            .AddSingleton(loggerFactory.Object)
            .BuildServiceProvider();
        var plugin = new KernelPlugin("plugin1");
        var plugins = new KernelPluginCollection() { plugin };
        Kernel kernel1 = new(serviceProvider, plugins);
        kernel1.Data["key"] = "value";

        // Clone and validate it
        Kernel kernel2 = kernel1.Clone();
        Assert.Same(kernel1.Services, kernel2.Services);
        Assert.Same(kernel1.Culture, kernel2.Culture);
        Assert.NotSame(kernel1.Data, kernel2.Data);
        Assert.Equal(kernel1.Data.Count, kernel2.Data.Count);
        Assert.Equal(kernel1.Data["key"], kernel2.Data["key"]);
        Assert.NotSame(kernel1.Plugins, kernel2.Plugins);
        Assert.Equal(kernel1.Plugins, kernel2.Plugins);

        // Minimally configured kernel
        Kernel kernel3 = new();

        // Clone and validate it
        Kernel kernel4 = kernel3.Clone();
        Assert.Same(kernel3.Services, kernel4.Services);
        Assert.NotSame(kernel3.Data, kernel4.Data);
        Assert.Empty(kernel4.Data);
        Assert.NotSame(kernel1.Plugins, kernel2.Plugins);
        Assert.Empty(kernel4.Plugins);
    }

    [Fact]
    public async Task InvokeStreamingAsyncCallsConnectorStreamingApiAsync()
    {
        // Arrange
        var mockTextCompletion = this.SetupStreamingMocks<StreamingContentBase>(
            new StreamingTextContent("chunk1"),
            new StreamingTextContent("chunk2"));
        var kernel = new KernelBuilder().WithServices(c => c.AddSingleton<ITextGenerationService>(mockTextCompletion.Object)).Build();
        var prompt = "Write a simple phrase about UnitTests {{$input}}";
        var sut = KernelFunctionFactory.CreateFromPrompt(prompt);
        var variables = new KernelArguments("importance");

        var chunkCount = 0;
        // Act
        await foreach (var chunk in sut.InvokeStreamingAsync<StreamingContentBase>(kernel, variables))
        {
            chunkCount++;
        }

        // Assert
        Assert.Equal(2, chunkCount);
        mockTextCompletion.Verify(m => m.GetStreamingTextContentsAsync(It.IsIn("Write a simple phrase about UnitTests importance"), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Exactly(1));
    }

    private (TextContent mockTextContent, Mock<ITextGenerationService> textCompletionMock) SetupMocks(string? completionResult = null)
    {
        var mockTextContent = new TextContent(completionResult ?? "LLM Result about UnitTests");

        var mockTextCompletion = new Mock<ITextGenerationService>();
        mockTextCompletion.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new List<TextContent> { mockTextContent });
        return (mockTextContent, mockTextCompletion);
    }

    private Mock<ITextGenerationService> SetupStreamingMocks<T>(params StreamingTextContent[] streamingContents)
    {
        var mockTextCompletion = new Mock<ITextGenerationService>();
        mockTextCompletion.Setup(m => m.GetStreamingTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).Returns(this.ToAsyncEnumerable(streamingContents));

        return mockTextCompletion;
    }

#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
#pragma warning disable IDE1006 // Naming Styles
    private async IAsyncEnumerable<T> ToAsyncEnumerable<T>(IEnumerable<T> enumeration)
#pragma warning restore IDE1006 // Naming Styles
#pragma warning restore CS1998 // Async method lacks 'await' operators and will run synchronously
    {
        foreach (var enumerationItem in enumeration)
        {
            yield return enumerationItem;
        }
    }

    public class MyPlugin
    {
        [KernelFunction, Description("Return any value.")]
        public virtual string GetAnyValue()
        {
            return Guid.NewGuid().ToString();
        }

        [KernelFunction, Description("Just say hello")]
        public virtual void SayHello()
        {
            Console.WriteLine("Hello folks!");
        }

        [KernelFunction("ReadFunctionCollectionAsync"), Description("Export info.")]
        public async Task ReadFunctionCollectionAsync(Kernel kernel)
        {
            await Task.Delay(0);
            Assert.NotNull(kernel.Plugins);
        }
    }
}

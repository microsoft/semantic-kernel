// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Globalization;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
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
        var factory = new Mock<Func<IServiceProvider, ITextCompletion>>();
        var kernel = new KernelBuilder().ConfigureServices(c =>
        {
            c.AddSingleton<ITextCompletion>(factory.Object);
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
        await Assert.ThrowsAsync<OperationCanceledException>(() => kernel.InvokeAsync(functions["GetAnyValue"], cancellationToken: cts.Token));
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
        var sut = new Kernel();
        int functionInvocations = 0;
        var function = KernelFunctionFactory.CreateFromMethod(() => functionInvocations++);

        var handlerInvocations = 0;
        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            handlerInvocations++;
        };

        // Act
        var result = await sut.InvokeAsync(function);

        // Assert
        Assert.Equal(1, functionInvocations);
        Assert.Equal(1, handlerInvocations);
    }

    [Fact]
    public async Task RunStreamingAsyncHandlesPreInvocationAsync()
    {
        // Arrange
        var sut = new Kernel();
        int functionInvocations = 0;
        var function = KernelFunctionFactory.CreateFromMethod(() => functionInvocations++);

        var handlerInvocations = 0;
        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            handlerInvocations++;
        };

        // Act
        await foreach (var chunk in sut.InvokeStreamingAsync(function)) { }

        // Assert
        Assert.Equal(1, functionInvocations);
        Assert.Equal(1, handlerInvocations);
    }

    [Fact]
    public async Task RunStreamingAsyncHandlesPreInvocationWasCancelledAsync()
    {
        // Arrange
        var sut = new Kernel();
        int functionInvocations = 0;
        var function = KernelFunctionFactory.CreateFromMethod(() => functionInvocations++);

        var handlerInvocations = 0;
        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            handlerInvocations++;
            e.Cancel();
        };

        // Act
        int chunksCount = 0;
        await foreach (var chunk in sut.InvokeStreamingAsync(function))
        {
            chunksCount++;
        }

        // Assert
        Assert.Equal(1, handlerInvocations);
        Assert.Equal(0, functionInvocations);
        Assert.Equal(0, chunksCount);
    }

    [Fact]
    public async Task RunStreamingAsyncPreInvocationCancelationDontTriggerInvokedHandlerAsync()
    {
        // Arrange
        var sut = new Kernel();
        var functions = sut.ImportPluginFromObject<MyPlugin>();

        var invoked = 0;
        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            e.Cancel();
        };

        sut.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            invoked++;
        };

        // Act
        await foreach (var chunk in sut.InvokeStreamingAsync(functions["GetAnyValue"]))
        {
        }

        // Assert
        Assert.Equal(0, invoked);
    }

    [Fact]
    public async Task RunStreamingAsyncPreInvocationSkipDontTriggerInvokedHandlerAsync()
    {
        // Arrange
        var sut = new Kernel();
        int funcInvocations = 0;
        var function = KernelFunctionFactory.CreateFromMethod(() => funcInvocations++, functionName: "func1");

        var invoked = 0;
        var invoking = 0;
        string invokedFunction = string.Empty;

        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            invoking++;
            if (e.Function.Name == "func1")
            {
                e.Skip();
            }
        };

        sut.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            invokedFunction = e.Function.Name;
            invoked++;
        };

        // Act
        await foreach (var chunk in sut.InvokeStreamingAsync(function))
        {
        }

        // Assert
        Assert.Equal(1, invoking);
        Assert.Equal(0, invoked);
        Assert.Equal(0, funcInvocations);
    }

    [Fact]
    public async Task InvokeStreamingAsyncDoesNotHandlePostInvocationAsync()
    {
        // Arrange
        var sut = new Kernel();
        int functionInvocations = 0;
        var function = KernelFunctionFactory.CreateFromMethod(() => functionInvocations++);

        int handlerInvocations = 0;
        sut.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            handlerInvocations++;
        };

        // Act
        await foreach (var chunk in sut.InvokeStreamingAsync(function))
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
        var sut = new Kernel();
        int functionInvocations = 0;
        var function = KernelFunctionFactory.CreateFromMethod(() => functionInvocations++);

        var handlerInvocations = 0;
        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            handlerInvocations++;
            e.Cancel();
        };

        // Act
        var result = await sut.InvokeAsync(function);

        // Assert
        Assert.Equal(1, handlerInvocations);
        Assert.Equal(0, functionInvocations);
        Assert.NotNull(result);
    }

    [Fact]
    public async Task InvokeAsyncHandlesPreInvocationCancelationDontRunSubsequentFunctionsInThePipelineAsync()
    {
        // Arrange
        var sut = new Kernel();
        int functionInvocations = 0;
        var function = KernelFunctionFactory.CreateFromMethod(() => functionInvocations++);

        int handlerInvocations = 0;
        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            handlerInvocations++;
            e.Cancel();
        };

        // Act
        var result = await sut.InvokeAsync(function);

        // Assert
        Assert.Equal(1, handlerInvocations);
        Assert.Equal(0, functionInvocations);
    }

    [Fact]
    public async Task InvokeAsyncPreInvocationCancelationDontTriggerInvokedHandlerAsync()
    {
        // Arrange
        var sut = new Kernel();
        var functions = sut.ImportPluginFromObject<MyPlugin>();

        var invoked = 0;
        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            e.Cancel();
        };

        sut.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            invoked++;
        };

        // Act
        var result = await sut.InvokeAsync(functions["GetAnyValue"]);

        // Assert
        Assert.Equal(0, invoked);
    }

    [Fact]
    public async Task InvokeAsyncPreInvocationSkipDontTriggerInvokedHandlerAsync()
    {
        // Arrange
        var sut = new Kernel();
        int funcInvocations = 0;
        var function = KernelFunctionFactory.CreateFromMethod(() => funcInvocations++, functionName: "func1");

        var invoked = 0;
        var invoking = 0;
        string invokedFunction = string.Empty;

        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            invoking++;
            if (e.Function.Name == "func1")
            {
                e.Skip();
            }
        };

        sut.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            invokedFunction = e.Function.Name;
            invoked++;
        };

        // Act
        var result = await sut.InvokeAsync(function);

        // Assert
        Assert.Equal(1, invoking);
        Assert.Equal(0, invoked);
        Assert.Equal(0, funcInvocations);
    }

    [Fact]
    public async Task InvokeAsyncHandlesPostInvocationAsync()
    {
        // Arrange
        var sut = new Kernel();
        int functionInvocations = 0;
        var function = KernelFunctionFactory.CreateFromMethod(() => functionInvocations++);

        int handlerInvocations = 0;
        sut.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            handlerInvocations++;
        };

        // Act
        var result = await sut.InvokeAsync(function);

        // Assert
        Assert.Equal(1, functionInvocations);
        Assert.Equal(1, handlerInvocations);
    }

    [Fact]
    public async Task InvokeAsyncChangeVariableInvokingHandlerAsync()
    {
        var sut = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => { });

        var originalInput = "Importance";
        var newInput = "Problems";

        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            originalInput = newInput;
        };

        // Act
        await sut.InvokeAsync(function, originalInput);

        // Assert
        Assert.Equal(newInput, originalInput);
    }

    [Fact]
    public async Task InvokeAsyncChangeVariableInvokedHandlerAsync()
    {
        var sut = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => { });

        var originalInput = "Importance";
        var newInput = "Problems";

        sut.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            originalInput = newInput;
        };

        // Act
        await sut.InvokeAsync(function, originalInput);

        // Assert
        Assert.Equal(newInput, originalInput);
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
    public void CurrentCultureShouldBeReturnedIfNoCultureWasAssociatedWithKernel()
    {
        //Arrange
        var kernel = new Kernel();

        //Act
        var culture = kernel.Culture;

        //Assert
        Assert.NotNull(culture);
        Assert.Equal(CultureInfo.CurrentCulture, culture);
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

            if (kernel.Plugins == null)
            {
                Assert.Fail("Functions collection is missing");
            }
        }
    }
}

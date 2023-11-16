// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Services;
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
        var factory = new Mock<Func<ILoggerFactory, ITextCompletion>>();
        var kernel = new KernelBuilder()
            .WithDefaultAIService<ITextCompletion>(factory.Object)
            .Build();

        var nativePlugin = new MyPlugin();
        kernel.ImportPluginFromObject(nativePlugin, "mySk");

        // Act & Assert - 3 functions, var name is not case sensitive
        Assert.True(kernel.Plugins.TryGetFunction("mySk", "sayhello", out _));
        Assert.True(kernel.Plugins.TryGetFunction("MYSK", "SayHello", out _));
        Assert.True(kernel.Plugins.TryGetFunction("mySk", "ReadFunctionCollectionAsync", out _));
        Assert.True(kernel.Plugins.TryGetFunction("MYSK", "ReadFunctionCollectionAsync", out _));
    }

    [Fact]
    public async Task RunAsyncDoesNotRunWhenCancelledAsync()
    {
        // Arrange
        var kernel = new KernelBuilder().Build();
        var nativePlugin = new MyPlugin();
        var functions = kernel.ImportPluginFromObject(nativePlugin, "mySk");

        using CancellationTokenSource cts = new();
        cts.Cancel();

        // Act
        await Assert.ThrowsAsync<OperationCanceledException>(() => kernel.RunAsync(cts.Token, functions["GetAnyValue"]));
    }

    [Fact]
    public async Task RunAsyncRunsWhenNotCancelledAsync()
    {
        // Arrange
        var kernel = new KernelBuilder().Build();
        var nativePlugin = new MyPlugin();
        kernel.ImportPluginFromObject(nativePlugin, "mySk");

        using CancellationTokenSource cts = new();

        // Act
        KernelResult result = await kernel.RunAsync(cts.Token, kernel.Plugins["mySk"]["GetAnyValue"]);

        // Assert
        Assert.False(string.IsNullOrEmpty(result.GetValue<string>()));
    }

    [Fact]
    public void ItImportsPluginsNotCaseSensitive()
    {
        // Act
        ISKPlugin plugin = new KernelBuilder().Build().ImportPluginFromObject(new MyPlugin(), "test");

        // Assert
        Assert.Equal(3, plugin.Count());
        Assert.True(plugin.Contains("GetAnyValue"));
        Assert.True(plugin.Contains("getanyvalue"));
        Assert.True(plugin.Contains("GETANYVALUE"));
    }

    [Fact]
    public void ItAllowsToImportTheSamePluginMultipleTimesWithDifferentNames()
    {
        // Arrange
        var kernel = new KernelBuilder().Build();

        // Act - Assert no exception occurs
        kernel.ImportPluginFromObject<MyPlugin>();
        kernel.ImportPluginFromObject<MyPlugin>("plugin1");
        kernel.ImportPluginFromObject<MyPlugin>("plugin2");
        kernel.ImportPluginFromObject<MyPlugin>("plugin3");
    }

    [Theory]
    [InlineData(1)]
    [InlineData(2)]
    public async Task RunAsyncHandlesPreInvocationAsync(int pipelineCount)
    {
        // Arrange
        var sut = new KernelBuilder().Build();
        var myPlugin = new Mock<MyPlugin>();
        var functions = sut.ImportPluginFromObject(myPlugin.Object, "MyPlugin");

        var invoked = 0;
        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            invoked++;
        };
        List<ISKFunction> pipeline = new();
        for (int i = 0; i < pipelineCount; i++)
        {
            pipeline.Add(functions["SayHello"]);
        }

        // Act
        var result = await sut.RunAsync(pipeline.ToArray());

        // Assert
        Assert.Equal(pipelineCount, invoked);
        myPlugin.Verify(m => m.SayHello(), Times.Exactly(pipelineCount));
    }

    [Fact]
    public async Task RunAsyncHandlesPreInvocationWasCancelledAsync()
    {
        // Arrange
        var sut = new KernelBuilder().Build();
        var functions = sut.ImportPluginFromObject<MyPlugin>();

        var invoked = false;
        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            invoked = true;
            e.Cancel();
        };

        // Act
        var result = await sut.RunAsync(functions["GetAnyValue"]);

        // Assert
        Assert.True(invoked);
        Assert.Null(result.GetValue<string>());
    }

    [Fact]
    public async Task RunAsyncHandlesPreInvocationCancelationDontRunSubsequentFunctionsInThePipelineAsync()
    {
        // Arrange
        var sut = new KernelBuilder().Build();
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        var myPlugin = new Mock<MyPlugin>();
        var functions = sut.ImportPluginFromObject(myPlugin.Object, "MyPlugin");

        var invoked = 0;
        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            invoked++;
            e.Cancel();
        };

        // Act
        var result = await sut.RunAsync(functions["GetAnyValue"], functions["SayHello"]);

        // Assert
        Assert.Equal(1, invoked);
        myPlugin.Verify(m => m.GetAnyValue(), Times.Never);
        myPlugin.Verify(m => m.SayHello(), Times.Never);
    }

    [Fact]
    public async Task RunAsyncPreInvocationCancelationDontTriggerInvokedHandlerAsync()
    {
        // Arrange
        var sut = new KernelBuilder().Build();
        var functions = sut.ImportPluginFromObject<MyPlugin>("MyPlugin");

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
        var result = await sut.RunAsync(functions["GetAnyValue"]);

        // Assert
        Assert.Equal(0, invoked);
    }

    [Fact]
    public async Task RunAsyncPreInvocationSkipDontTriggerInvokedHandlerAsync()
    {
        // Arrange
        var sut = new KernelBuilder().Build();
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        var myPlugin = new Mock<MyPlugin>();
        var functions = sut.ImportPluginFromObject(myPlugin.Object, "MyPlugin");

        var invoked = 0;
        var invoking = 0;
        string invokedFunction = string.Empty;

        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            invoking++;
            if (e.FunctionView.Name == "GetAnyValue")
            {
                e.Skip();
            }
        };

        sut.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            invokedFunction = e.FunctionView.Name;
            invoked++;
        };

        // Act
        var result = await sut.RunAsync(functions["GetAnyValue"], functions["SayHello"]);

        // Assert
        Assert.Equal(2, invoking);
        Assert.Equal(1, invoked);
        myPlugin.Verify(m => m.GetAnyValue(), Times.Never);
        myPlugin.Verify(m => m.SayHello(), Times.Once);
    }

    [Theory]
    [InlineData(1)]
    [InlineData(2)]
    public async Task RunAsyncHandlesPostInvocationAsync(int pipelineCount)
    {
        // Arrange
        var sut = new KernelBuilder().Build();
        var myPlugin = new Mock<MyPlugin>();
        var functions = sut.ImportPluginFromObject(myPlugin.Object, "MyPlugin");

        var invoked = 0;
        sut.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            invoked++;
        };

        List<ISKFunction> pipeline = new();
        for (int i = 0; i < pipelineCount; i++)
        {
            pipeline.Add(functions["GetAnyValue"]);
        }

        // Act
        var result = await sut.RunAsync(pipeline.ToArray());

        // Assert
        Assert.Equal(pipelineCount, invoked);
        myPlugin.Verify(m => m.GetAnyValue(), Times.Exactly(pipelineCount));
    }

    [Fact]
    public async Task RunAsyncChangeVariableInvokingHandlerAsync()
    {
        var sut = new KernelBuilder().Build();
        var myPlugin = new Mock<MyPlugin>();
        var functions = sut.ImportPluginFromObject(myPlugin.Object, "MyPlugin");

        var originalInput = "Importance";
        var newInput = "Problems";

        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            originalInput = newInput;
        };

        // Act
        await sut.RunAsync(originalInput, functions["GetAnyValue"]);

        // Assert
        Assert.Equal(newInput, originalInput);
    }

    [Fact]
    public async Task RunAsyncChangeVariableInvokedHandlerAsync()
    {
        var sut = new KernelBuilder().Build();
        var myPlugin = new Mock<MyPlugin>();
        var functions = sut.ImportPluginFromObject(myPlugin.Object, "MyPlugin");

        var originalInput = "Importance";
        var newInput = "Problems";

        sut.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            originalInput = newInput;
        };

        // Act
        await sut.RunAsync(originalInput, functions["GetAnyValue"]);

        // Assert
        Assert.Equal(newInput, originalInput);
    }

    [Fact]
    public async Task ItReturnsFunctionResultsCorrectlyAsync()
    {
        // Arrange
        var kernel = new KernelBuilder().Build();

        var function1 = kernel.CreateFunctionFromMethod(() => "Result1", "Function1");
        var function2 = kernel.CreateFunctionFromMethod(() => "Result2", "Function2");

        // Act
        var kernelResult = await kernel.RunAsync(function1, function2);
        var functionResult1 = kernelResult.FunctionResults.First(l => l.FunctionName == "Function1");
        var functionResult2 = kernelResult.FunctionResults.First(l => l.FunctionName == "Function2");

        // Assert
        Assert.NotNull(kernelResult);
        Assert.Equal("Result2", kernelResult.GetValue<string>());
        Assert.Equal("Result1", functionResult1.GetValue<string>());
        Assert.Equal("Result2", functionResult2.GetValue<string>());
    }

    [Fact]
    public async Task ItReturnsChangedResultsFromFunctionInvokedEventsAsync()
    {
        var kernel = new KernelBuilder().Build();

        // Arrange
        var function1 = kernel.CreateFunctionFromMethod(() => "Result1", "Function1");
        const string ExpectedValue = "new result";

        kernel.FunctionInvoked += (object? sender, FunctionInvokedEventArgs args) =>
        {
            args.SKContext.Variables.Update(ExpectedValue);
        };

        // Act
        var kernelResult = await kernel.RunAsync(function1);

        // Assert
        Assert.NotNull(kernelResult);
        Assert.Equal(ExpectedValue, kernelResult.GetValue<string>());
        Assert.Equal(ExpectedValue, kernelResult.FunctionResults.Single().GetValue<string>());
        Assert.Equal(ExpectedValue, kernelResult.FunctionResults.Single().Context.Result);
    }

    [Fact]
    public async Task ItReturnsChangedResultsFromFunctionInvokingEventsAsync()
    {
        // Arrange
        var kernel = new KernelBuilder().Build();

        var function1 = kernel.CreateFunctionFromMethod((string injectedVariable) => injectedVariable, "Function1");
        const string ExpectedValue = "injected value";

        kernel.FunctionInvoking += (object? sender, FunctionInvokingEventArgs args) =>
        {
            args.SKContext.Variables["injectedVariable"] = ExpectedValue;
        };

        // Act
        var kernelResult = await kernel.RunAsync(function1);

        // Assert
        Assert.NotNull(kernelResult);
        Assert.Equal(ExpectedValue, kernelResult.GetValue<string>());
        Assert.Equal(ExpectedValue, kernelResult.FunctionResults.Single().GetValue<string>());
        Assert.Equal(ExpectedValue, kernelResult.FunctionResults.Single().Context.Result);
    }

    [Theory]
    [InlineData("Function1", 5)]
    [InlineData("Function2", 1)]
    public async Task ItRepeatsFunctionInvokedEventsAsync(string retryFunction, int numberOfRepeats)
    {
        // Arrange
        var kernel = new KernelBuilder().Build();

        var function1 = kernel.CreateFunctionFromMethod(() => "Result1", "Function1");
        var function2 = kernel.CreateFunctionFromMethod(() => "Result2", "Function2");

        int numberOfInvocations = 0;
        int repeatCount = 0;

        kernel.FunctionInvoked += (object? sender, FunctionInvokedEventArgs args) =>
        {
            if (args.FunctionView.Name == retryFunction && repeatCount < numberOfRepeats)
            {
                args.Repeat();
                repeatCount++;
            }

            numberOfInvocations++;
        };

        // Act
        var kernelResult = await kernel.RunAsync(function1, function2);

        // Assert
        Assert.NotNull(kernelResult);
        Assert.Equal(2 + numberOfRepeats, kernelResult.FunctionResults.Count);
        Assert.Equal(2 + numberOfRepeats, numberOfInvocations);
    }

    [Theory]
    [InlineData("Function1", "Result2 Result3")]
    [InlineData("Function2", "Result1 Result3")]
    [InlineData("Function3", "Result1 Result2")]
    public async Task ItSkipsFunctionsFromFunctionInvokingEventsAsync(string skipFunction, string expectedResult)
    {
        // Arrange
        var kernel = new KernelBuilder().Build();

        var function1 = kernel.CreateFunctionFromMethod((string input) => $"{input} Result1", "Function1");
        var function2 = kernel.CreateFunctionFromMethod((string input) => $"{input} Result2", "Function2");
        var function3 = kernel.CreateFunctionFromMethod((string input) => $"{input} Result3", "Function3");

        const int ExpectedInvocations = 2;

        int numberOfInvocations = 0;

        kernel.FunctionInvoking += (object? sender, FunctionInvokingEventArgs args) =>
        {
            if (args.FunctionView.Name == skipFunction)
            {
                args.Skip();
            }
        };

        kernel.FunctionInvoked += (object? sender, FunctionInvokedEventArgs args) =>
        {
            numberOfInvocations++;
        };

        // Act
        var kernelResult = await kernel.RunAsync(string.Empty, function1, function2, function3);

        // Assert
        Assert.NotNull(kernelResult);
        Assert.Equal(expectedResult, kernelResult.GetValue<string>()!.Trim());
        Assert.Equal(ExpectedInvocations, numberOfInvocations);

        // ExpectedInvocations
        Assert.Equal(ExpectedInvocations, kernelResult.FunctionResults.Count);
    }

    [Theory]
    [InlineData(1, 0, 0)]
    [InlineData(2, 0, 0)]
    [InlineData(2, 1, 1)]
    [InlineData(5, 2, 2)]
    public async Task ItCancelsPipelineFromFunctionInvokingEventsAsync(int numberOfFunctions, int functionCancelIndex, int invokedHandlerInvocations)
    {
        var kernel = new KernelBuilder().Build();

        // Arrange
        List<ISKFunction> functions = new()
        {
            kernel.CreateFunctionFromMethod(() => "Result1", "Function1"),
            kernel.CreateFunctionFromMethod(() => "Result2", "Function2"),
            kernel.CreateFunctionFromMethod(() => "Result3", "Function3"),
            kernel.CreateFunctionFromMethod(() => "Result4", "Function4"),
            kernel.CreateFunctionFromMethod(() => "Result5", "Function5")
        };

        int numberOfInvocations = 0;

        kernel.FunctionInvoking += (object? sender, FunctionInvokingEventArgs args) =>
        {
            if (args.FunctionView.Name == functions[functionCancelIndex].Name)
            {
                args.Cancel();
            }
        };

        kernel.FunctionInvoked += (object? sender, FunctionInvokedEventArgs args) =>
        {
            numberOfInvocations++;
        };

        // Act
        var kernelResult = await kernel.RunAsync(functions.Take(numberOfFunctions).ToArray());

        // Assert
        Assert.NotNull(kernelResult);

        // Kernel result is the same as the last invoked function
        Assert.Equal(invokedHandlerInvocations, numberOfInvocations);

        // Number of invocations
        Assert.Equal(numberOfInvocations, kernelResult.FunctionResults.Count);
    }

    [Theory]
    [InlineData(1, 0, 1)]
    [InlineData(2, 0, 1)]
    [InlineData(2, 1, 2)]
    [InlineData(5, 2, 3)]
    public async Task ItCancelsPipelineFromFunctionInvokedEventsAsync(int numberOfFunctions, int functionCancelIndex, int expectedInvocations)
    {
        var kernel = new KernelBuilder().Build();

        // Arrange
        List<ISKFunction> functions = new()
        {
            kernel.CreateFunctionFromMethod(() => "Result1", "Function1"),
            kernel.CreateFunctionFromMethod(() => "Result2", "Function2"),
            kernel.CreateFunctionFromMethod(() => "Result3", "Function3"),
            kernel.CreateFunctionFromMethod(() => "Result4", "Function4"),
            kernel.CreateFunctionFromMethod(() => "Result5", "Function5")
        };

        int numberOfInvocations = 0;

        kernel.FunctionInvoked += (object? sender, FunctionInvokedEventArgs args) =>
        {
            numberOfInvocations++;
            if (args.FunctionView.Name == functions[functionCancelIndex].Name)
            {
                args.Cancel();
            }
        };

        // Act
        var kernelResult = await kernel.RunAsync(functions.Take(numberOfFunctions).ToArray());

        // Assert
        Assert.NotNull(kernelResult);

        if (functionCancelIndex == 0)
        {
            // If the first function was cancelled, the result should be null
            Assert.Null(kernelResult.GetValue<string>());
        }
        else
        {
            // Else result should be of the last invoked function
            Assert.Equal($"Result{functionCancelIndex}", kernelResult.GetValue<string>());
        }
        Assert.Equal(expectedInvocations, numberOfInvocations);
    }

    [Fact]
    public async Task ItCanFindAndRunFunctionAsync()
    {
        //Arrange
        var serviceProvider = new Mock<IAIServiceProvider>();
        var serviceSelector = new Mock<IAIServiceSelector>();

        var context = new SKContext(new Kernel(serviceProvider.Object), serviceProvider.Object, serviceSelector.Object, new ContextVariables());

        var function = SKFunction.FromMethod(() => "fake result", "function");

        var kernel = new Kernel(new Mock<IAIServiceProvider>().Object);
        kernel.Plugins.Add(new SKPlugin("plugin", new[] { function }));

        //Act
        var result = await kernel.RunAsync("plugin", "function");

        //Assert
        Assert.NotNull(result);
        Assert.Equal("fake result", result.GetValue<string>());
    }

    public class MyPlugin
    {
        [SKFunction, Description("Return any value.")]
        public virtual string GetAnyValue()
        {
            return Guid.NewGuid().ToString();
        }

        [SKFunction, Description("Just say hello")]
        public virtual void SayHello()
        {
            Console.WriteLine("Hello folks!");
        }

        [SKFunction, Description("Export info."), SKName("ReadFunctionCollectionAsync")]
        public async Task<SKContext> ReadFunctionCollectionAsync(SKContext context)
        {
            await Task.Delay(0);

            if (context.Plugins == null)
            {
                Assert.Fail("Functions collection is missing");
            }

            foreach (var function in context.Plugins.GetFunctionViews())
            {
                context.Variables[$"{function.PluginName}.{function.Name}"] = function.Description;
            }

            return context;
        }
    }

    private (Mock<ITextResult> textResultMock, Mock<ITextCompletion> textCompletionMock) SetupMocks(string? completionResult = null)
    {
        var mockTextResult = new Mock<ITextResult>();
        mockTextResult.Setup(m => m.GetCompletionAsync(It.IsAny<CancellationToken>())).ReturnsAsync(completionResult ?? "LLM Result about UnitTests");

        var mockTextCompletion = new Mock<ITextCompletion>();
        mockTextCompletion.Setup(m => m.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new List<ITextResult> { mockTextResult.Object });

        return (mockTextResult, mockTextCompletion);
    }

    private static MethodInfo Method(Delegate method)
    {
        return method.Method;
    }
}

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
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SemanticFunctions;
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
        var kernel = Kernel.Builder
            .WithDefaultAIService<ITextCompletion>(factory.Object)
            .Build();

        var nativePlugin = new MyPlugin();
        kernel.CreateSemanticFunction(promptTemplate: "Tell me a joke", functionName: "joker", pluginName: "jk", description: "Nice fun");
        kernel.ImportFunctions(nativePlugin, "mySk");

        // Act & Assert - 3 functions, var name is not case sensitive
        Assert.True(kernel.Functions.TryGetFunction("jk", "joker", out _));
        Assert.True(kernel.Functions.TryGetFunction("JK", "JOKER", out _));
        Assert.True(kernel.Functions.TryGetFunction("mySk", "sayhello", out _));
        Assert.True(kernel.Functions.TryGetFunction("MYSK", "SayHello", out _));
        Assert.True(kernel.Functions.TryGetFunction("mySk", "ReadFunctionCollectionAsync", out _));
        Assert.True(kernel.Functions.TryGetFunction("MYSK", "ReadFunctionCollectionAsync", out _));
    }

    [Fact]
    public async Task RunAsyncDoesNotRunWhenCancelledAsync()
    {
        // Arrange
        var kernel = Kernel.Builder.Build();
        var nativePlugin = new MyPlugin();
        var functions = kernel.ImportFunctions(nativePlugin, "mySk");

        using CancellationTokenSource cts = new();
        cts.Cancel();

        // Act
        await Assert.ThrowsAsync<OperationCanceledException>(() => kernel.RunAsync(cts.Token, functions["GetAnyValue"]));
    }

    [Fact]
    public async Task RunAsyncRunsWhenNotCancelledAsync()
    {
        // Arrange
        var kernel = Kernel.Builder.Build();
        var nativePlugin = new MyPlugin();
        kernel.ImportFunctions(nativePlugin, "mySk");

        using CancellationTokenSource cts = new();

        // Act
        KernelResult result = await kernel.RunAsync(cts.Token, kernel.Functions.GetFunction("mySk", "GetAnyValue"));

        // Assert
        Assert.False(string.IsNullOrEmpty(result.GetValue<string>()));
    }

    [Fact]
    public void ItImportsPluginsNotCaseSensitive()
    {
        // Act
        IDictionary<string, ISKFunction> functions = Kernel.Builder.Build().ImportFunctions(new MyPlugin(), "test");

        // Assert
        Assert.Equal(3, functions.Count);
        Assert.True(functions.ContainsKey("GetAnyValue"));
        Assert.True(functions.ContainsKey("getanyvalue"));
        Assert.True(functions.ContainsKey("GETANYVALUE"));
    }

    [Theory]
    [InlineData(null, "Assistant is a large language model.", true)]
    [InlineData("My Chat Prompt", "My Chat Prompt", false)]
    public async Task ItUsesChatSystemPromptWhenProvidedAsync(string providedSystemChatPrompt, string expectedSystemChatPrompt, bool useStream)
    {
        // Arrange
        var mockTextCompletion = new Mock<ITextCompletion>();
        var mockCompletionResult = new Mock<ITextStreamingResult>();

        mockTextCompletion.Setup(c => c.GetStreamingCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).Returns(new[] { mockCompletionResult.Object }.ToAsyncEnumerable());
        mockTextCompletion.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockCompletionResult.Setup(cr => cr.GetCompletionStreamingAsync(It.IsAny<CancellationToken>())).Returns(new[] { "llmResult" }.ToAsyncEnumerable());
        mockCompletionResult.Setup(cr => cr.GetCompletionAsync(It.IsAny<CancellationToken>())).ReturnsAsync("llmResult");

        var kernel = Kernel.Builder
            .WithAIService<ITextCompletion>("x", mockTextCompletion.Object)
            .Build();

        var templateConfig = new PromptTemplateConfig
        {
            Completion = new OpenAIRequestSettings()
            {
                ChatSystemPrompt = providedSystemChatPrompt,
                Streaming = useStream
            }
        };

        var func = kernel.CreateSemanticFunction("template", templateConfig, "functionName", "pluginName");

        // Act
        await kernel.RunAsync(func);

        // Assert
        if (useStream)
        {
            mockTextCompletion.Verify(a => a.GetStreamingCompletionsAsync("template", It.Is<OpenAIRequestSettings>(c => c.ChatSystemPrompt == expectedSystemChatPrompt), It.IsAny<CancellationToken>()), Times.Once());
        }
        else
        {
            mockTextCompletion.Verify(a => a.GetCompletionsAsync("template", It.Is<OpenAIRequestSettings>(c => c.ChatSystemPrompt == expectedSystemChatPrompt), It.IsAny<CancellationToken>()), Times.Once());
        }
    }

    [Fact]
    public void ItAllowsToImportFunctionsInTheGlobalNamespace()
    {
        // Arrange
        var kernel = Kernel.Builder.Build();

        // Act
        IDictionary<string, ISKFunction> functions = kernel.ImportFunctions(new MyPlugin());

        // Assert
        Assert.Equal(3, functions.Count);
        Assert.True(kernel.Functions.TryGetFunction("GetAnyValue", out ISKFunction? functionInstance));
        Assert.NotNull(functionInstance);
    }

    [Fact]
    public void ItAllowsToImportTheSamePluginMultipleTimes()
    {
        // Arrange
        var kernel = Kernel.Builder.Build();

        // Act - Assert no exception occurs
        kernel.ImportFunctions(new MyPlugin());
        kernel.ImportFunctions(new MyPlugin());
        kernel.ImportFunctions(new MyPlugin());
    }

    [Theory]
    [InlineData(null)]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItUsesDefaultServiceWhenSpecifiedAsync(bool? useStream)
    {
        // Arrange
        var mockTextCompletion1 = new Mock<ITextCompletion>();
        var mockTextCompletion2 = new Mock<ITextCompletion>();
        var mockCompletionResult = new Mock<ITextStreamingResult>();

        mockTextCompletion1.Setup(c => c.GetStreamingCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).Returns(new[] { mockCompletionResult.Object }.ToAsyncEnumerable());
        mockTextCompletion1.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });

        mockTextCompletion2.Setup(c => c.GetStreamingCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).Returns(new[] { mockCompletionResult.Object }.ToAsyncEnumerable());
        mockTextCompletion2.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });

        mockCompletionResult.Setup(cr => cr.GetCompletionStreamingAsync(It.IsAny<CancellationToken>())).Returns(new[] { "llmResult" }.ToAsyncEnumerable());
        mockCompletionResult.Setup(cr => cr.GetCompletionAsync(It.IsAny<CancellationToken>())).ReturnsAsync("llmResult");

        var kernel = Kernel.Builder
            .WithAIService<ITextCompletion>("service1", mockTextCompletion1.Object, false)
            .WithAIService<ITextCompletion>("service2", mockTextCompletion2.Object, true)
            .Build();

        var templateConfig = new PromptTemplateConfig();
        if (useStream is not null)
        {
            templateConfig.Completion = new() { Streaming = useStream };
        };

        var func = kernel.CreateSemanticFunction("template", templateConfig, "functionName", "pluginName");

        // Act
        await kernel.RunAsync(func);

        // Assert
        if (useStream is null)
        {
            mockTextCompletion1.Verify(a => a.GetCompletionsAsync("template", null, It.IsAny<CancellationToken>()), Times.Never());
            mockTextCompletion2.Verify(a => a.GetCompletionsAsync("template", null, It.IsAny<CancellationToken>()), Times.Once());
        }
        else if (useStream == false)
        {
            mockTextCompletion1.Verify(a => a.GetCompletionsAsync("template", It.Is<AIRequestSettings>(rs => rs.Streaming == useStream), It.IsAny<CancellationToken>()), Times.Never());
            mockTextCompletion2.Verify(a => a.GetCompletionsAsync("template", It.Is<AIRequestSettings>(rs => rs.Streaming == useStream), It.IsAny<CancellationToken>()), Times.Once());
        }
        else
        {
            mockTextCompletion1.Verify(a => a.GetStreamingCompletionsAsync("template", It.Is<AIRequestSettings>(rs => rs.Streaming == useStream), It.IsAny<CancellationToken>()), Times.Never());
            mockTextCompletion2.Verify(a => a.GetStreamingCompletionsAsync("template", It.Is<AIRequestSettings>(rs => rs.Streaming == useStream), It.IsAny<CancellationToken>()), Times.Once());
        }
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ItUsesServiceIdWhenProvidedAsync(bool useStream)
    {
        // Arrange
        var mockTextCompletion1 = new Mock<ITextCompletion>();
        var mockTextCompletion2 = new Mock<ITextCompletion>();
        var mockCompletionResult = new Mock<ITextStreamingResult>();

        mockTextCompletion1.Setup(c => c.GetStreamingCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).Returns(new[] { mockCompletionResult.Object }.ToAsyncEnumerable());
        mockTextCompletion1.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });

        mockTextCompletion2.Setup(c => c.GetStreamingCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).Returns(new[] { mockCompletionResult.Object }.ToAsyncEnumerable());
        mockTextCompletion2.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });

        mockCompletionResult.Setup(cr => cr.GetCompletionStreamingAsync(It.IsAny<CancellationToken>())).Returns(new[] { "llmResult" }.ToAsyncEnumerable());
        mockCompletionResult.Setup(cr => cr.GetCompletionAsync(It.IsAny<CancellationToken>())).ReturnsAsync("llmResult");

        var kernel = Kernel.Builder
            .WithAIService<ITextCompletion>("service1", mockTextCompletion1.Object, false)
            .WithAIService<ITextCompletion>("service2", mockTextCompletion2.Object, true)
            .Build();

        var templateConfig = new PromptTemplateConfig
        {
            Completion = new AIRequestSettings() { ServiceId = "service1", Streaming = useStream }
        };
        var func = kernel.CreateSemanticFunction("template", templateConfig, "functionName", "pluginName");

        // Act
        await kernel.RunAsync(func);

        // Assert
        if (useStream)
        {
            mockTextCompletion1.Verify(a => a.GetStreamingCompletionsAsync("template", It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()), Times.Once());
            mockTextCompletion2.Verify(a => a.GetStreamingCompletionsAsync("template", It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()), Times.Never());
        }
        else
        {
            mockTextCompletion1.Verify(a => a.GetCompletionsAsync("template", It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()), Times.Once());
            mockTextCompletion2.Verify(a => a.GetCompletionsAsync("template", It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()), Times.Never());
        }
    }

    [Fact]
    public async Task ItFailsIfInvalidServiceIdIsProvidedAsync()
    {
        // Arrange
        var mockTextCompletion1 = new Mock<ITextCompletion>();
        var mockTextCompletion2 = new Mock<ITextCompletion>();

        var kernel = Kernel.Builder
            .WithAIService<ITextCompletion>("service1", mockTextCompletion1.Object, false)
            .WithAIService<ITextCompletion>("service2", mockTextCompletion2.Object, true)
            .Build();

        var templateConfig = new PromptTemplateConfig
        {
            Completion = new AIRequestSettings() { ServiceId = "service3" }
        };
        var func = kernel.CreateSemanticFunction("template", templateConfig, "functionName", "pluginName");

        // Act
        var exception = await Assert.ThrowsAsync<SKException>(() => kernel.RunAsync(func));

        // Assert
        Assert.Equal("Service of type Microsoft.SemanticKernel.AI.TextCompletion.ITextCompletion and name service3 not registered.", exception.Message);
    }

    [Theory]
    [InlineData(1, true)]
    [InlineData(2, false)]
    public async Task RunAsyncHandlesPreInvocationAsync(int pipelineCount, bool useStream)
    {
        // Arrange
        var sut = Kernel.Builder.Build();
        var semanticFunction = sut.CreateSemanticFunction("Write a simple phrase about UnitTests", requestSettings: new() { Streaming = useStream });
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();

        semanticFunction.SetAIService(() => mockTextCompletion.Object);
        var invoked = 0;
        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            invoked++;
        };
        List<ISKFunction> functions = new();
        for (int i = 0; i < pipelineCount; i++)
        {
            functions.Add(semanticFunction);
        }

        // Act
        var result = await sut.RunAsync(functions.ToArray());

        // Assert
        Assert.Equal(pipelineCount, invoked);
        if (useStream)
        {
            mockTextCompletion.Verify(m => m.GetStreamingCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()), Times.Exactly(pipelineCount));
        }
        else
        {
            mockTextCompletion.Verify(m => m.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()), Times.Exactly(pipelineCount));
        }
    }

    [Fact]
    public async Task RunAsyncHandlesPreInvocationWasCancelledAsync()
    {
        // Arrange
        var sut = Kernel.Builder.Build();
        var semanticFunction = sut.CreateSemanticFunction("Write a simple phrase about UnitTests");
        var input = "Test input";
        var invoked = false;
        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            invoked = true;
            e.Cancel();
        };

        // Act
        var result = await sut.RunAsync(input, semanticFunction);

        // Assert
        Assert.True(invoked);
        Assert.Null(result.GetValue<string>());
    }

    [Fact]
    public async Task RunAsyncHandlesPreInvocationCancelationDontRunSubsequentFunctionsInThePipelineAsync()
    {
        // Arrange
        var sut = Kernel.Builder.Build();
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        var semanticFunction = sut.CreateSemanticFunction("Write a simple phrase about UnitTests");
        semanticFunction.SetAIService(() => mockTextCompletion.Object);

        var invoked = 0;
        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            invoked++;
            e.Cancel();
        };

        // Act
        var result = await sut.RunAsync(semanticFunction, semanticFunction);

        // Assert
        Assert.Equal(1, invoked);
        mockTextCompletion.Verify(m => m.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()), Times.Never);
    }

    [Fact]
    public async Task RunAsyncPreInvocationCancelationDontTriggerInvokedHandlerAsync()
    {
        // Arrange
        var sut = Kernel.Builder.Build();
        var semanticFunction = sut.CreateSemanticFunction("Write a simple phrase about UnitTests");
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
        var result = await sut.RunAsync(semanticFunction);

        // Assert
        Assert.Equal(0, invoked);
    }

    [Fact]
    public async Task RunAsyncPreInvocationSkipDontTriggerInvokedHandlerAsync()
    {
        // Arrange
        var sut = Kernel.Builder.Build();
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        var semanticFunction1 = sut.CreateSemanticFunction("Write one phrase about UnitTests", functionName: "SkipMe");
        var semanticFunction2 = sut.CreateSemanticFunction("Write two phrases about UnitTests", functionName: "DontSkipMe");
        semanticFunction2.SetAIService(() => mockTextCompletion.Object);
        var invoked = 0;
        var invoking = 0;
        string invokedFunction = string.Empty;

        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            invoking++;
            if (e.FunctionView.Name == "SkipMe")
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
        var result = await sut.RunAsync(
            semanticFunction1,
            semanticFunction2);

        // Assert
        Assert.Equal(2, invoking);
        Assert.Equal(1, invoked);
        Assert.Equal("DontSkipMe", invokedFunction);
    }

    [Theory]
    [InlineData(1, null)]
    [InlineData(1, true)]
    [InlineData(1, false)]
    [InlineData(2, null)]
    [InlineData(2, true)]
    [InlineData(2, false)]
    public async Task RunAsyncHandlesPostInvocationAsync(int pipelineCount, bool? useStream)
    {
        // Arrange
        var sut = Kernel.Builder.Build();
        AIRequestSettings? requestSettings = (useStream is null) ? null : new() { Streaming = useStream };
        var semanticFunction = sut.CreateSemanticFunction("Write a simple phrase about UnitTests", requestSettings: requestSettings);

        var (mockTextResult, mockTextCompletion) = this.SetupMocks();

        semanticFunction.SetAIService(() => mockTextCompletion.Object);
        var invoked = 0;

        sut.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            invoked++;
        };

        List<ISKFunction> functions = new();
        for (int i = 0; i < pipelineCount; i++)
        {
            functions.Add(semanticFunction);
        }

        // Act
        var result = await sut.RunAsync(functions.ToArray());

        // Assert
        Assert.Equal(pipelineCount, invoked);
        if (useStream == true)
        {
            mockTextCompletion.Verify(m => m.GetStreamingCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()), Times.Exactly(pipelineCount));
        }
        else
        {
            mockTextCompletion.Verify(m => m.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()), Times.Exactly(pipelineCount));
        }
    }

    [Fact]
    public async Task RunAsyncChangeVariableInvokingHandlerAsync()
    {
        var sut = Kernel.Builder.Build();
        var prompt = "Write a simple phrase about UnitTests {{$input}}";
        var semanticFunction = sut.CreateSemanticFunction(prompt);
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        semanticFunction.SetAIService(() => mockTextCompletion.Object);

        var originalInput = "Importance";
        var newInput = "Problems";

        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            originalInput = newInput;
        };

        // Act
        await sut.RunAsync(originalInput, semanticFunction);

        // Assert
        Assert.Equal(newInput, originalInput);
    }

    [Fact]
    public async Task RunAsyncChangeVariableInvokedHandlerAsync()
    {
        var sut = Kernel.Builder.Build();
        var prompt = "Write a simple phrase about UnitTests {{$input}}";
        var semanticFunction = sut.CreateSemanticFunction(prompt);
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        semanticFunction.SetAIService(() => mockTextCompletion.Object);

        var originalInput = "Importance";
        var newInput = "Problems";

        sut.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            originalInput = newInput;
        };

        // Act
        await sut.RunAsync(originalInput, semanticFunction);

        // Assert
        Assert.Equal(newInput, originalInput);
    }

    [Fact]
    public async Task ItReturnsFunctionResultsCorrectlyAsync()
    {
        // Arrange
        [SKName("Function1")]
        static string Function1() => "Result1";

        [SKName("Function2")]
        static string Function2() => "Result2";

        const string PluginName = "MyPlugin";
        const string Prompt = "Write a simple phrase about UnitTests";

        var kernel = Kernel.Builder.Build();

        var function1 = SKFunction.FromNativeMethod(Method(Function1), pluginName: PluginName);
        var function2 = SKFunction.FromNativeMethod(Method(Function2), pluginName: PluginName);

        var function3 = kernel.CreateSemanticFunction(Prompt, functionName: "Function3", pluginName: PluginName);
        var (mockTextResult, mockTextCompletion) = this.SetupMocks("Result3");

        function3.SetAIService(() => mockTextCompletion.Object);

        // Act
        var kernelResult = await kernel.RunAsync(function1, function2, function3);

        // Assert
        Assert.NotNull(kernelResult);
        Assert.Equal("Result3", kernelResult.GetValue<string>());

        var functionResult1 = kernelResult.FunctionResults.First(l => l.FunctionName == "Function1" && l.PluginName == PluginName);
        var functionResult2 = kernelResult.FunctionResults.First(l => l.FunctionName == "Function2" && l.PluginName == PluginName);
        var functionResult3 = kernelResult.FunctionResults.First(l => l.FunctionName == "Function3" && l.PluginName == PluginName);

        Assert.Equal("Result1", functionResult1.GetValue<string>());
        Assert.Equal("Result2", functionResult2.GetValue<string>());
        Assert.Equal("Result3", functionResult3.GetValue<string>());
    }

    [Fact]
    public async Task ItReturnsStreamingFunctionResultsCorrectlyAsync()
    {
        // Arrange
        [SKName("Function1")]
        static string Function1() => "Result1";

        [SKName("Function2")]
        static string Function2() => "Result2";

        const string PluginName = "MyPlugin";
        const string Prompt = "Write a simple phrase about UnitTests";

        var kernel = Kernel.Builder.Build();

        var function1 = SKFunction.FromNativeMethod(Method(Function1), pluginName: PluginName);
        var function2 = SKFunction.FromNativeMethod(Method(Function2), pluginName: PluginName);

        var function3 = kernel.CreateSemanticFunction(Prompt, functionName: "Function3", pluginName: PluginName, requestSettings: new()
        {
            Streaming = true
        });

        var (mockTextResult, mockTextCompletion) = this.SetupMocks("Result3");

        function3.SetAIService(() => mockTextCompletion.Object);

        // Act
        var kernelResult = await kernel.RunAsync(function1, function2, function3);

        // Assert
        Assert.NotNull(kernelResult);

        var functionResult1 = kernelResult.FunctionResults.First(l => l.FunctionName == "Function1" && l.PluginName == PluginName);
        var functionResult2 = kernelResult.FunctionResults.First(l => l.FunctionName == "Function2" && l.PluginName == PluginName);
        var functionResult3 = kernelResult.FunctionResults.First(l => l.FunctionName == "Function3" && l.PluginName == PluginName);

        var function3Result = functionResult3.GetValue<string>();
        Assert.Equal("Result1", functionResult1.GetValue<string>());
        Assert.Equal("Result2", functionResult2.GetValue<string>());
        Assert.Equal("Result3", function3Result);

        var resultText = string.Join(string.Empty, kernelResult.GetValue<IAsyncEnumerable<string>>()!.ToEnumerable());
        Assert.Equal("Result3", resultText);

        var function3ResultStreamText = string.Join(string.Empty, functionResult3.GetValue<IAsyncEnumerable<string>>()!.ToEnumerable());
        Assert.Equal("Result3", function3ResultStreamText);
    }

    public class MyPlugin
    {
        [SKFunction, Description("Return any value.")]
        public string GetAnyValue()
        {
            return Guid.NewGuid().ToString();
        }

        [SKFunction, Description("Just say hello")]
        public void SayHello()
        {
            Console.WriteLine("Hello folks!");
        }

        [SKFunction, Description("Export info."), SKName("ReadFunctionCollectionAsync")]
        public async Task<SKContext> ReadFunctionCollectionAsync(SKContext context)
        {
            await Task.Delay(0);

            if (context.Functions == null)
            {
                Assert.Fail("Functions collection is missing");
            }

            foreach (var function in context.Functions.GetFunctionViews())
            {
                context.Variables[$"{function.PluginName}.{function.Name}"] = function.Description;
            }

            return context;
        }
    }

    private (Mock<ITextStreamingResult> textResultMock, Mock<ITextCompletion> textCompletionMock) SetupMocks(string? completionResult = null)
    {
        var mockTextResult = new Mock<ITextStreamingResult>();
        mockTextResult.Setup(m => m.GetCompletionStreamingAsync(It.IsAny<CancellationToken>())).Returns(() => new List<string> { completionResult ?? "LLM Result about UnitTests" }.ToAsyncEnumerable());
        mockTextResult.Setup(m => m.GetCompletionAsync(It.IsAny<CancellationToken>())).ReturnsAsync(completionResult ?? "LLM Result about UnitTests");

        var mockTextCompletion = new Mock<ITextCompletion>();
        mockTextCompletion.Setup(m => m.GetStreamingCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).Returns(new List<ITextStreamingResult> { mockTextResult.Object }.ToAsyncEnumerable());
        mockTextCompletion.Setup(m => m.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new List<ITextStreamingResult> { mockTextResult.Object });

        return (mockTextResult, mockTextCompletion);
    }

    private static MethodInfo Method(Delegate method)
    {
        return method.Method;
    }
}

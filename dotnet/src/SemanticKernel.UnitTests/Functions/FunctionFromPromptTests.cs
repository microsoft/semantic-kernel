// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Orchestration;
using Moq;
using Xunit;

// ReSharper disable StringLiteralTypo

namespace SemanticKernel.UnitTests.Functions;

public class FunctionFromPromptTests
{
    [Fact]
    public void ItProvidesAccessToFunctionsViaFunctionCollection()
    {
        // Arrange
        var factory = new Mock<Func<ILoggerFactory, ITextCompletion>>();
        var kernel = new KernelBuilder()
            .WithDefaultAIService(factory.Object)
            .Build();

        kernel.Plugins.Add(new KernelPlugin("jk", functions: new[] { kernel.CreateFunctionFromPrompt(promptTemplate: "Tell me a joke", functionName: "joker", description: "Nice fun") }));

        // Act & Assert - 3 functions, var name is not case sensitive
        Assert.True(kernel.Plugins.TryGetFunction("jk", "joker", out _));
        Assert.True(kernel.Plugins.TryGetFunction("JK", "JOKER", out _));
    }

    [Theory]
    [InlineData(null, "Assistant is a large language model.")]
    [InlineData("My Chat Prompt", "My Chat Prompt")]
    public async Task ItUsesChatSystemPromptWhenProvidedAsync(string providedSystemChatPrompt, string expectedSystemChatPrompt)
    {
        // Arrange
        var mockTextCompletion = new Mock<ITextCompletion>();
        var mockCompletionResult = new Mock<ITextResult>();

        mockTextCompletion.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockCompletionResult.Setup(cr => cr.GetCompletionAsync(It.IsAny<CancellationToken>())).ReturnsAsync("llmResult");

        var kernel = new KernelBuilder()
            .WithAIService("x", mockTextCompletion.Object)
            .Build();

        var templateConfig = new PromptTemplateConfig();
        templateConfig.ModelSettings.Add(new OpenAIRequestSettings()
        {
            ChatSystemPrompt = providedSystemChatPrompt
        });

        var func = kernel.CreateFunctionFromPrompt("template", templateConfig, "pluginName");

        // Act
        await kernel.InvokeAsync(func);

        // Assert
        mockTextCompletion.Verify(a => a.GetCompletionsAsync("template", It.Is<OpenAIRequestSettings>(c => c.ChatSystemPrompt == expectedSystemChatPrompt), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task ItUsesDefaultServiceWhenSpecifiedAsync()
    {
        // Arrange
        var mockTextCompletion1 = new Mock<ITextCompletion>();
        var mockTextCompletion2 = new Mock<ITextCompletion>();
        var mockCompletionResult = new Mock<ITextResult>();

        mockTextCompletion1.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), null, It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockTextCompletion2.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), null, It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockCompletionResult.Setup(cr => cr.GetCompletionAsync(It.IsAny<CancellationToken>())).ReturnsAsync("llmResult");

        var kernel = new KernelBuilder()
            .WithAIService("service1", mockTextCompletion1.Object, false)
            .WithAIService("service2", mockTextCompletion2.Object, true)
            .Build();

        var templateConfig = new PromptTemplateConfig();
        var func = kernel.CreateFunctionFromPrompt("template", templateConfig, "pluginName");

        // Act
        await kernel.InvokeAsync(func);

        // Assert
        mockTextCompletion1.Verify(a => a.GetCompletionsAsync("template", null, It.IsAny<CancellationToken>()), Times.Never());
        mockTextCompletion2.Verify(a => a.GetCompletionsAsync("template", null, It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task ItUsesServiceIdWhenProvidedAsync()
    {
        // Arrange
        var mockTextCompletion1 = new Mock<ITextCompletion>();
        var mockTextCompletion2 = new Mock<ITextCompletion>();
        var mockCompletionResult = new Mock<ITextResult>();

        mockTextCompletion1.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockTextCompletion2.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockCompletionResult.Setup(cr => cr.GetCompletionAsync(It.IsAny<CancellationToken>())).ReturnsAsync("llmResult");

        var kernel = new KernelBuilder()
            .WithAIService("service1", mockTextCompletion1.Object, false)
            .WithAIService("service2", mockTextCompletion2.Object, true)
            .Build();

        var templateConfig = new PromptTemplateConfig();
        templateConfig.ModelSettings.Add(new AIRequestSettings() { ServiceId = "service1" });
        var func = kernel.CreateFunctionFromPrompt("template", templateConfig, "pluginName");

        // Act
        await kernel.InvokeAsync(func);

        // Assert
        mockTextCompletion1.Verify(a => a.GetCompletionsAsync("template", It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()), Times.Once());
        mockTextCompletion2.Verify(a => a.GetCompletionsAsync("template", It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()), Times.Never());
    }

    [Fact]
    public async Task ItFailsIfInvalidServiceIdIsProvidedAsync()
    {
        // Arrange
        var mockTextCompletion1 = new Mock<ITextCompletion>();
        var mockTextCompletion2 = new Mock<ITextCompletion>();

        var kernel = new KernelBuilder()
            .WithAIService("service1", mockTextCompletion1.Object, false)
            .WithAIService("service2", mockTextCompletion2.Object, true)
            .Build();

        var templateConfig = new PromptTemplateConfig();
        templateConfig.ModelSettings.Add(new AIRequestSettings() { ServiceId = "service3" });
        var func = kernel.CreateFunctionFromPrompt("template", templateConfig, "pluginName");

        // Act
        var exception = await Assert.ThrowsAsync<KernelException>(() => kernel.InvokeAsync(func));

        // Assert
        Assert.Equal("Service of type Microsoft.SemanticKernel.AI.TextCompletion.ITextCompletion and name service3 not registered.", exception.Message);
    }

    [Fact]
    public async Task RunAsyncHandlesPreInvocationAsync()
    {
        // Arrange
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        var sut = new KernelBuilder().WithAIService<ITextCompletion>(null, mockTextCompletion.Object).Build();
        var function = KernelFunctionFactory.CreateFromPrompt("Write a simple phrase about UnitTests");

        var invoked = 0;
        sut.FunctionInvoking += (sender, e) =>
        {
            invoked++;
        };
        List<KernelFunction> functions = new();

        // Act
        var result = await sut.InvokeAsync(function);

        // Assert
        Assert.Equal(1, invoked);
        mockTextCompletion.Verify(m => m.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()), Times.Exactly(1));
    }

    [Fact]
    public async Task RunAsyncHandlesPreInvocationWasCancelledAsync()
    {
        // Arrange
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        var sut = new KernelBuilder().WithAIService<ITextCompletion>(null, mockTextCompletion.Object).Build();
        var function = KernelFunctionFactory.CreateFromPrompt("Write a simple phrase about UnitTests");
        var input = "Test input";
        var invoked = false;
        sut.FunctionInvoking += (sender, e) =>
        {
            invoked = true;
            e.Cancel();
        };

        // Act
        var result = await sut.InvokeAsync(function, input);

        // Assert
        Assert.True(invoked);
        Assert.NotNull(result);
    }

    [Fact]
    public async Task RunAsyncHandlesPreInvocationCancelationDontRunSubsequentFunctionsInThePipelineAsync()
    {
        // Arrange
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        var sut = new KernelBuilder().WithAIService<ITextCompletion>(null, mockTextCompletion.Object).Build();
        var function = KernelFunctionFactory.CreateFromPrompt("Write a simple phrase about UnitTests");

        var invoked = 0;
        sut.FunctionInvoking += (sender, e) =>
        {
            invoked++;
            e.Cancel();
        };

        // Act
        var result = await sut.InvokeAsync(function);

        // Assert
        Assert.Equal(1, invoked);
        mockTextCompletion.Verify(m => m.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()), Times.Never);
    }

    [Fact]
    public async Task RunAsyncPreInvocationCancelationDontTriggerInvokedHandlerAsync()
    {
        // Arrange
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        var sut = new KernelBuilder().WithAIService<ITextCompletion>(null, mockTextCompletion.Object).Build();
        var function = KernelFunctionFactory.CreateFromPrompt("Write a simple phrase about UnitTests");
        var invoked = 0;

        sut.FunctionInvoking += (sender, e) =>
        {
            e.Cancel();
        };

        sut.FunctionInvoked += (sender, e) =>
        {
            invoked++;
        };

        // Act
        var result = await sut.InvokeAsync(function);

        // Assert
        Assert.Equal(0, invoked);
    }

    [Fact]
    public async Task RunAsyncPreInvocationSkipDontTriggerInvokedHandlerAsync()
    {
        // Arrange
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        var sut = new KernelBuilder().WithAIService<ITextCompletion>(null, mockTextCompletion.Object).Build();
        var function = KernelFunctionFactory.CreateFromPrompt("Write one phrase about UnitTests", functionName: "SkipMe");
        var invoked = 0;
        var invoking = 0;
        string invokedFunction = string.Empty;

        sut.FunctionInvoking += (sender, e) =>
        {
            invoking++;
            if (e.Function.GetMetadata().Name == "SkipMe")
            {
                e.Skip();
            }
        };

        sut.FunctionInvoked += (sender, e) =>
        {
            invokedFunction = e.Function.GetMetadata().Name;
            invoked++;
        };

        // Act
        var result = await sut.InvokeAsync(function);

        // Assert
        Assert.Equal(1, invoking);
        Assert.Equal(0, invoked);
        Assert.Equal("", invokedFunction);
    }

    [Fact]
    public async Task RunAsyncHandlesPostInvocationAsync()
    {
        // Arrange
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        var sut = new KernelBuilder().WithAIService<ITextCompletion>(null, mockTextCompletion.Object).Build();
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
        mockTextCompletion.Verify(m => m.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()), Times.Exactly(1));
    }

    [Fact]
    public async Task RunAsyncChangeVariableInvokingHandlerAsync()
    {
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        var sut = new KernelBuilder().WithAIService<ITextCompletion>(null, mockTextCompletion.Object).Build();
        var prompt = "Write a simple phrase about UnitTests {{$input}}";
        var function = KernelFunctionFactory.CreateFromPrompt(prompt);

        var originalInput = "Importance";
        var newInput = "Problems";

        sut.FunctionInvoking += (sender, e) =>
        {
            originalInput = newInput;
        };

        // Act
        await sut.InvokeAsync(function, originalInput);

        // Assert
        Assert.Equal(newInput, originalInput);
    }

    [Fact]
    public async Task RunAsyncChangeVariableInvokedHandlerAsync()
    {
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        var sut = new KernelBuilder().WithAIService<ITextCompletion>(null, mockTextCompletion.Object).Build();
        var prompt = "Write a simple phrase about UnitTests {{$input}}";
        var function = KernelFunctionFactory.CreateFromPrompt(prompt);

        var originalInput = "Importance";
        var newInput = "Problems";

        sut.FunctionInvoked += (sender, e) =>
        {
            originalInput = newInput;
        };

        // Act
        await sut.InvokeAsync(function, originalInput);

        // Assert
        Assert.Equal(newInput, originalInput);
    }

    [Fact]
    public async Task InvokeStreamingAsyncCallsConnectorStreamingApiAsync()
    {
        // Arrange
        var mockTextCompletion = this.SetupStreamingMocks<StreamingContent>(
            new TestStreamingContent("chunk1"),
            new TestStreamingContent("chunk2"));
        var kernel = new KernelBuilder().WithAIService<ITextCompletion>(null, mockTextCompletion.Object).Build();
        var prompt = "Write a simple phrase about UnitTests {{$input}}";
        var sut = KernelFunctionFactory.CreateFromPrompt(prompt);
        var variables = new ContextVariables("importance");

        var chunkCount = 0;
        // Act
        await foreach (var chunk in sut.InvokeStreamingAsync<StreamingContent>(kernel, variables))
        {
            chunkCount++;
        }

        // Assert
        Assert.Equal(2, chunkCount);
        mockTextCompletion.Verify(m => m.GetStreamingContentAsync<StreamingContent>(It.IsIn("Write a simple phrase about UnitTests importance"), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()), Times.Exactly(1));
    }

    private (Mock<ITextResult> textResultMock, Mock<ITextCompletion> textCompletionMock) SetupMocks(string? completionResult = null)
    {
        var mockTextResult = new Mock<ITextResult>();
        mockTextResult.Setup(m => m.GetCompletionAsync(It.IsAny<CancellationToken>())).ReturnsAsync(completionResult ?? "LLM Result about UnitTests");

        var mockTextCompletion = new Mock<ITextCompletion>();
        mockTextCompletion.Setup(m => m.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new List<ITextResult> { mockTextResult.Object });
        return (mockTextResult, mockTextCompletion);
    }

    private Mock<ITextCompletion> SetupStreamingMocks<T>(params T[] completionResults)
    {
        var mockTextCompletion = new Mock<ITextCompletion>();
        mockTextCompletion.Setup(m => m.GetStreamingContentAsync<T>(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).Returns(this.ToAsyncEnumerable(completionResults));

        return mockTextCompletion;
    }

    private sealed class TestStreamingContent : StreamingContent
    {
        private readonly string _content;

        public TestStreamingContent(string content) : base(null)
        {
            this._content = content;
        }

        public override int ChoiceIndex => 0;

        public override byte[] ToByteArray()
        {
            return Array.Empty<byte>();
        }

        public override string ToString()
        {
            return this._content;
        }
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
}

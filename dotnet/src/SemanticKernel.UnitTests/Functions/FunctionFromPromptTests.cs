// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
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
        var factory = new Mock<Func<IServiceProvider, ITextCompletion>>();
        var kernel = new KernelBuilder().WithServices(c =>
        {
            c.AddSingleton(factory.Object);
        }).Build();

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

        mockTextCompletion.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockCompletionResult.Setup(cr => cr.GetCompletionAsync(It.IsAny<CancellationToken>())).ReturnsAsync("llmResult");

        var kernel = new KernelBuilder().WithServices(c =>
        {
            c.AddKeyedSingleton("x", mockTextCompletion.Object);
        }).Build();

        var promptConfig = new PromptTemplateConfig();
        promptConfig.Template = "template";
        promptConfig.ExecutionSettings.Add(new OpenAIPromptExecutionSettings()
        {
            ChatSystemPrompt = providedSystemChatPrompt
        });

        var func = kernel.CreateFunctionFromPrompt(promptConfig);

        // Act
        await kernel.InvokeAsync(func);

        // Assert
        mockTextCompletion.Verify(a => a.GetCompletionsAsync("template", It.Is<OpenAIPromptExecutionSettings>(c => c.ChatSystemPrompt == expectedSystemChatPrompt), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task ItUsesServiceIdWhenProvidedAsync()
    {
        // Arrange
        var mockTextCompletion1 = new Mock<ITextCompletion>();
        var mockTextCompletion2 = new Mock<ITextCompletion>();
        var mockCompletionResult = new Mock<ITextResult>();

        mockTextCompletion1.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockTextCompletion2.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockCompletionResult.Setup(cr => cr.GetCompletionAsync(It.IsAny<CancellationToken>())).ReturnsAsync("llmResult");

        var kernel = new KernelBuilder().WithServices(c =>
        {
            c.AddKeyedSingleton("service1", mockTextCompletion1.Object);
            c.AddKeyedSingleton("service2", mockTextCompletion2.Object);
        }).Build();

        var promptConfig = new PromptTemplateConfig();
        promptConfig.Template = "template";
        promptConfig.ExecutionSettings.Add(new PromptExecutionSettings() { ServiceId = "service1" });
        var func = kernel.CreateFunctionFromPrompt(promptConfig);

        // Act
        await kernel.InvokeAsync(func);

        // Assert
        mockTextCompletion1.Verify(a => a.GetCompletionsAsync("template", It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
        mockTextCompletion2.Verify(a => a.GetCompletionsAsync("template", It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Never());
    }

    [Fact]
    public async Task ItFailsIfInvalidServiceIdIsProvidedAsync()
    {
        // Arrange
        var mockTextCompletion1 = new Mock<ITextCompletion>();
        var mockTextCompletion2 = new Mock<ITextCompletion>();

        var kernel = new KernelBuilder().WithServices(c =>
        {
            c.AddKeyedSingleton("service1", mockTextCompletion1.Object);
            c.AddKeyedSingleton("service2", mockTextCompletion2.Object);
        }).Build();

        var promptConfig = new PromptTemplateConfig();
        promptConfig.Template = "template";
        promptConfig.ExecutionSettings.Add(new PromptExecutionSettings() { ServiceId = "service3" });
        var func = kernel.CreateFunctionFromPrompt(promptConfig);

        // Act
        var exception = await Assert.ThrowsAsync<KernelException>(() => kernel.InvokeAsync(func));

        // Assert
        Assert.Equal("Service of type Microsoft.SemanticKernel.AI.TextCompletion.ITextCompletion and names service3 not registered.", exception.Message);
    }

    [Fact]
    public async Task InvokeAsyncHandlesPreInvocationAsync()
    {
        // Arrange
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        var sut = new KernelBuilder().WithServices(c => c.AddSingleton<ITextCompletion>(mockTextCompletion.Object)).Build();
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
        mockTextCompletion.Verify(m => m.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Exactly(1));
    }

    [Fact]
    public async Task InvokeAsyncHandlesPreInvocationWasCancelledAsync()
    {
        // Arrange
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        var sut = new KernelBuilder().WithServices(c => c.AddSingleton<ITextCompletion>(mockTextCompletion.Object)).Build();
        var function = KernelFunctionFactory.CreateFromPrompt("Write a simple phrase about UnitTests");
        var input = "Test input";
        var invoked = false;
        sut.FunctionInvoking += (sender, e) =>
        {
            invoked = true;
            e.Cancel = true;
        };

        // Act
        var result = await sut.InvokeAsync(function, input);

        // Assert
        Assert.True(invoked);
        Assert.NotNull(result);
    }

    [Fact]
    public async Task InvokeAsyncHandlesPreInvocationCancelationDontRunSubsequentFunctionsInThePipelineAsync()
    {
        // Arrange
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        var sut = new KernelBuilder().WithServices(c => c.AddSingleton<ITextCompletion>(mockTextCompletion.Object)).Build();
        var function = KernelFunctionFactory.CreateFromPrompt("Write a simple phrase about UnitTests");

        var invoked = 0;
        sut.FunctionInvoking += (sender, e) =>
        {
            invoked++;
            e.Cancel = true;
        };

        // Act
        var result = await sut.InvokeAsync(function);

        // Assert
        Assert.Equal(1, invoked);
        mockTextCompletion.Verify(m => m.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Never);
    }

    [Fact]
    public async Task InvokeAsyncPreInvocationCancelationDontTriggerInvokedHandlerAsync()
    {
        // Arrange
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        var sut = new KernelBuilder().WithServices(c => c.AddSingleton<ITextCompletion>(mockTextCompletion.Object)).Build();
        var function = KernelFunctionFactory.CreateFromPrompt("Write a simple phrase about UnitTests");
        var invoked = 0;

        sut.FunctionInvoking += (sender, e) =>
        {
            e.Cancel = true;
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
    public async Task InvokeAsyncHandlesPostInvocationAsync()
    {
        // Arrange
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        var sut = new KernelBuilder().WithServices(c => c.AddSingleton<ITextCompletion>(mockTextCompletion.Object)).Build();
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
        mockTextCompletion.Verify(m => m.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Exactly(1));
    }

    [Fact]
    public async Task InvokeAsyncChangeVariableInvokingHandlerAsync()
    {
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        var sut = new KernelBuilder().WithServices(c => c.AddSingleton<ITextCompletion>(mockTextCompletion.Object)).Build();
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
    public async Task InvokeAsyncChangeVariableInvokedHandlerAsync()
    {
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        var sut = new KernelBuilder().WithServices(c => c.AddSingleton<ITextCompletion>(mockTextCompletion.Object)).Build();
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
        var kernel = new KernelBuilder().WithServices(c => c.AddSingleton<ITextCompletion>(mockTextCompletion.Object)).Build();
        var prompt = "Write a simple phrase about UnitTests {{$input}}";
        var sut = KernelFunctionFactory.CreateFromPrompt(prompt);
        var variables = new KernelArguments { { "input", "importance" } };

        var chunkCount = 0;
        // Act
        await foreach (var chunk in sut.InvokeStreamingAsync<StreamingContent>(kernel, variables))
        {
            chunkCount++;
        }

        // Assert
        Assert.Equal(2, chunkCount);
        mockTextCompletion.Verify(m => m.GetStreamingContentAsync<StreamingContent>(It.IsIn("Write a simple phrase about UnitTests importance"), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Exactly(1));
    }

    private (Mock<ITextResult> textResultMock, Mock<ITextCompletion> textCompletionMock) SetupMocks(string? completionResult = null)
    {
        var mockTextResult = new Mock<ITextResult>();
        mockTextResult.Setup(m => m.GetCompletionAsync(It.IsAny<CancellationToken>())).ReturnsAsync(completionResult ?? "LLM Result about UnitTests");

        var mockTextCompletion = new Mock<ITextCompletion>();
        mockTextCompletion.Setup(m => m.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new List<ITextResult> { mockTextResult.Object });
        return (mockTextResult, mockTextCompletion);
    }

    private Mock<ITextCompletion> SetupStreamingMocks<T>(params T[] completionResults)
    {
        var mockTextCompletion = new Mock<ITextCompletion>();
        mockTextCompletion.Setup(m => m.GetStreamingContentAsync<T>(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).Returns(this.ToAsyncEnumerable(completionResults));

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

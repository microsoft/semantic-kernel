// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextGeneration;
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
        var factory = new Mock<Func<IServiceProvider, ITextGenerationService>>();
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
        var mockTextGeneration = new Mock<ITextGenerationService>();
        var fakeTextContent = new TextContent("llmResult");

        mockTextGeneration.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { fakeTextContent });

        var kernel = new KernelBuilder().WithServices(c =>
        {
            c.AddKeyedSingleton("x", mockTextGeneration.Object);
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
        mockTextGeneration.Verify(a => a.GetTextContentsAsync("template", It.Is<OpenAIPromptExecutionSettings>(c => c.ChatSystemPrompt == expectedSystemChatPrompt), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task ItUsesServiceIdWhenProvidedAsync()
    {
        // Arrange
        var mockTextGeneration1 = new Mock<ITextGenerationService>();
        var mockTextGeneration2 = new Mock<ITextGenerationService>();
        var fakeTextContent = new TextContent("llmResult");

        mockTextGeneration1.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { fakeTextContent });
        mockTextGeneration2.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { fakeTextContent });

        var kernel = new KernelBuilder().WithServices(c =>
        {
            c.AddKeyedSingleton("service1", mockTextGeneration1.Object);
            c.AddKeyedSingleton("service2", mockTextGeneration2.Object);
        }).Build();

        var promptConfig = new PromptTemplateConfig();
        promptConfig.Template = "template";
        promptConfig.ExecutionSettings.Add(new PromptExecutionSettings() { ServiceId = "service1" });
        var func = kernel.CreateFunctionFromPrompt(promptConfig);

        // Act
        await kernel.InvokeAsync(func);

        // Assert
        mockTextGeneration1.Verify(a => a.GetTextContentsAsync("template", It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
        mockTextGeneration2.Verify(a => a.GetTextContentsAsync("template", It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Never());
    }

    [Fact]
    public async Task ItFailsIfInvalidServiceIdIsProvidedAsync()
    {
        // Arrange
        var mockTextGeneration1 = new Mock<ITextGenerationService>();
        var mockTextGeneration2 = new Mock<ITextGenerationService>();

        var kernel = new KernelBuilder().WithServices(c =>
        {
            c.AddKeyedSingleton("service1", mockTextGeneration1.Object);
            c.AddKeyedSingleton("service2", mockTextGeneration2.Object);
        }).Build();

        var promptConfig = new PromptTemplateConfig();
        promptConfig.Template = "template";
        promptConfig.ExecutionSettings.Add(new PromptExecutionSettings() { ServiceId = "service3" });
        var func = kernel.CreateFunctionFromPrompt(promptConfig);

        // Act
        var exception = await Assert.ThrowsAsync<KernelException>(() => kernel.InvokeAsync(func));

        // Assert
        Assert.Equal("Service of type Microsoft.SemanticKernel.AI.TextGeneration.ITextGenerationService and names service3 not registered.", exception.Message);
    }

    [Fact]
    public async Task InvokeAsyncHandlesPreInvocationAsync()
    {
        // Arrange
        var (mockTextResult, mockTextGeneration) = this.SetupMocks();
        var sut = new KernelBuilder().WithServices(c => c.AddSingleton<ITextGenerationService>(mockTextGeneration.Object)).Build();
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
        mockTextGeneration.Verify(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Exactly(1));
    }

    [Fact]
    public async Task InvokeAsyncHandlesPreInvocationWasCancelledAsync()
    {
        // Arrange
        var (mockTextResult, mockTextGeneration) = this.SetupMocks();
        var sut = new KernelBuilder().WithServices(c => c.AddSingleton<ITextGenerationService>(mockTextGeneration.Object)).Build();
        var function = KernelFunctionFactory.CreateFromPrompt("Write a simple phrase about UnitTests");
        var input = "Test input";
        var invoked = false;
        sut.FunctionInvoking += (sender, e) =>
        {
            invoked = true;
            e.Cancel = true;
        };

        // Act
        KernelFunctionCanceledException ex = await Assert.ThrowsAsync<KernelFunctionCanceledException>(() => sut.InvokeAsync(function, input));

        // Assert
        Assert.True(invoked);
        Assert.Same(function, ex.Function);
        Assert.Null(ex.FunctionResult);
    }

    [Fact]
    public async Task InvokeAsyncHandlesPreInvocationCancelationDontRunSubsequentFunctionsInThePipelineAsync()
    {
        // Arrange
        var (mockTextResult, mockTextGeneration) = this.SetupMocks();
        var sut = new KernelBuilder().WithServices(c => c.AddSingleton<ITextGenerationService>(mockTextGeneration.Object)).Build();
        var function = KernelFunctionFactory.CreateFromPrompt("Write a simple phrase about UnitTests");

        var invoked = 0;
        sut.FunctionInvoking += (sender, e) =>
        {
            invoked++;
            e.Cancel = true;
        };

        // Act/Assert
        KernelFunctionCanceledException ex = await Assert.ThrowsAsync<KernelFunctionCanceledException>(() => sut.InvokeAsync(function));

        // Assert
        Assert.Equal(1, invoked);
        mockTextGeneration.Verify(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Never);
        Assert.Same(function, ex.Function);
    }

    [Fact]
    public async Task InvokeAsyncPreInvocationCancelationDontTriggerInvokedHandlerAsync()
    {
        // Arrange
        var (mockTextResult, mockTextGeneration) = this.SetupMocks();
        var sut = new KernelBuilder().WithServices(c => c.AddSingleton<ITextGenerationService>(mockTextGeneration.Object)).Build();
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
        await Assert.ThrowsAsync<KernelFunctionCanceledException>(() => sut.InvokeAsync(function));

        // Assert
        Assert.Equal(0, invoked);
    }

    [Fact]
    public async Task InvokeAsyncHandlesPostInvocationAsync()
    {
        // Arrange
        var (mockTextResult, mockTextGeneration) = this.SetupMocks();
        var sut = new KernelBuilder().WithServices(c => c.AddSingleton<ITextGenerationService>(mockTextGeneration.Object)).Build();
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
        mockTextGeneration.Verify(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Exactly(1));
    }

    [Fact]
    public async Task InvokeAsyncChangeVariableInvokingHandlerAsync()
    {
        var (mockTextResult, mockTextGeneration) = this.SetupMocks();
        var sut = new KernelBuilder().WithServices(c => c.AddSingleton<ITextGenerationService>(mockTextGeneration.Object)).Build();
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
        var (mockTextResult, mockTextGeneration) = this.SetupMocks();
        var sut = new KernelBuilder().WithServices(c => c.AddSingleton<ITextGenerationService>(mockTextGeneration.Object)).Build();
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
        var mockTextGeneration = this.SetupStreamingMocks<StreamingContentBase>(
            new StreamingTextContent("chunk1"),
            new StreamingTextContent("chunk2"));
        var kernel = new KernelBuilder().WithServices(c => c.AddSingleton<ITextGenerationService>(mockTextGeneration.Object)).Build();
        var prompt = "Write a simple phrase about UnitTests {{$input}}";
        var sut = KernelFunctionFactory.CreateFromPrompt(prompt);
        var variables = new KernelArguments { { "input", "importance" } };

        var chunkCount = 0;
        // Act
        await foreach (var chunk in sut.InvokeStreamingAsync<StreamingContentBase>(kernel, variables))
        {
            chunkCount++;
        }

        // Assert
        Assert.Equal(2, chunkCount);
        mockTextGeneration.Verify(m => m.GetStreamingTextContentsAsync(It.IsIn("Write a simple phrase about UnitTests importance"), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Exactly(1));
    }

    private (TextContent mockTextContent, Mock<ITextGenerationService> textCompletionMock) SetupMocks(string? completionResult = null)
    {
        var mockTextContent = new TextContent(completionResult ?? "LLM Result about UnitTests");

        var mockTextGenerationService = new Mock<ITextGenerationService>();
        mockTextGenerationService.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new List<TextContent> { mockTextContent });
        return (mockTextContent, mockTextGenerationService);
    }

    private Mock<ITextGenerationService> SetupStreamingMocks<T>(params StreamingTextContent[] streamingContents)
    {
        var mockTextGenerationService = new Mock<ITextGenerationService>();
        mockTextGenerationService.Setup(m => m.GetStreamingTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).Returns(this.ToAsyncEnumerable(streamingContents));

        return mockTextGenerationService;
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

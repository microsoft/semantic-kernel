// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.TemplateEngine;
using Moq;
using Xunit;

// ReSharper disable StringLiteralTypo

namespace SemanticKernel.UnitTests.Functions;

public class SemanticFunctionTests
{
    [Fact]
    public void ItProvidesAccessToFunctionsViaFunctionCollection()
    {
        // Arrange
        var factory = new Mock<Func<ILoggerFactory, ITextCompletion>>();
        var kernel = new KernelBuilder()
            .WithDefaultAIService(factory.Object)
            .Build();

        kernel.CreateSemanticFunction(promptTemplate: "Tell me a joke", functionName: "joker", pluginName: "jk", description: "Nice fun");

        // Act & Assert - 3 functions, var name is not case sensitive
        Assert.True(kernel.Functions.TryGetFunction("jk", "joker", out _));
        Assert.True(kernel.Functions.TryGetFunction("JK", "JOKER", out _));
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

        var func = kernel.CreateSemanticFunction("template", templateConfig, "functionName", "pluginName");

        // Act
        await kernel.RunAsync(func);

        // Assert
        mockTextCompletion.Verify(a => a.GetCompletionsAsync("template", It.Is<OpenAIRequestSettings>(c => c.ChatSystemPrompt == expectedSystemChatPrompt), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public void ItAllowsToCreateFunctionsInTheGlobalNamespace()
    {
        // Arrange
        var kernel = new KernelBuilder().Build();
        var templateConfig = new PromptTemplateConfig();

        // Act
        var func = kernel.CreateSemanticFunction("template", templateConfig, "functionName");

        // Assert
        Assert.Equal(FunctionCollection.GlobalFunctionsPluginName, func.PluginName);
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
        var func = kernel.CreateSemanticFunction("template", templateConfig, "functionName", "pluginName");

        // Act
        await kernel.RunAsync(func);

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
        var func = kernel.CreateSemanticFunction("template", templateConfig, "functionName", "pluginName");

        // Act
        await kernel.RunAsync(func);

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
        var func = kernel.CreateSemanticFunction("template", templateConfig, "functionName", "pluginName");

        // Act
        var exception = await Assert.ThrowsAsync<SKException>(() => kernel.RunAsync(func));

        // Assert
        Assert.Equal("Service of type Microsoft.SemanticKernel.AI.TextCompletion.ITextCompletion and name service3 not registered.", exception.Message);
    }

    [Theory]
    [InlineData(1)]
    [InlineData(2)]
    public async Task RunAsyncHandlesPreInvocationAsync(int pipelineCount)
    {
        // Arrange
        var mockTextCompletion = this.SetupTextCompletionMock();
        var sut = new KernelBuilder().WithAIService<ITextCompletion>(null, mockTextCompletion.Object).Build();
        var semanticFunction = sut.CreateSemanticFunction("Write a simple phrase about UnitTests");

        var invoked = 0;
        sut.FunctionInvoking += (sender, e) =>
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
        mockTextCompletion.Verify(m => m.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()), Times.Exactly(pipelineCount));
    }

    [Fact]
    public async Task RunAsyncHandlesPreInvocationWasCancelledAsync()
    {
        // Arrange
        var sut = new KernelBuilder().Build();
        var semanticFunction = sut.CreateSemanticFunction("Write a simple phrase about UnitTests");
        var input = "Test input";
        var invoked = false;
        sut.FunctionInvoking += (sender, e) =>
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
        var mockTextCompletion = this.SetupTextCompletionMock();
        var sut = new KernelBuilder().WithAIService<ITextCompletion>(null, mockTextCompletion.Object).Build();
        var semanticFunction = sut.CreateSemanticFunction("Write a simple phrase about UnitTests");

        var invoked = 0;
        sut.FunctionInvoking += (sender, e) =>
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
        var sut = new KernelBuilder().Build();
        var semanticFunction = sut.CreateSemanticFunction("Write a simple phrase about UnitTests");
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
        var result = await sut.RunAsync(semanticFunction);

        // Assert
        Assert.Equal(0, invoked);
    }

    [Fact]
    public async Task RunAsyncPreInvocationSkipDontTriggerInvokedHandlerAsync()
    {
        // Arrange
        var mockTextCompletion = this.SetupTextCompletionMock();
        var sut = new KernelBuilder().WithAIService<ITextCompletion>(null, mockTextCompletion.Object).Build();
        var semanticFunction1 = sut.CreateSemanticFunction("Write one phrase about UnitTests", functionName: "SkipMe");
        var semanticFunction2 = sut.CreateSemanticFunction("Write two phrases about UnitTests", functionName: "DontSkipMe");
        var invoked = 0;
        var invoking = 0;
        string invokedFunction = string.Empty;

        sut.FunctionInvoking += (sender, e) =>
        {
            invoking++;
            if (e.FunctionView.Name == "SkipMe")
            {
                e.Skip();
            }
        };

        sut.FunctionInvoked += (sender, e) =>
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
    [InlineData(1)]
    [InlineData(2)]
    public async Task RunAsyncHandlesPostInvocationAsync(int pipelineCount)
    {
        // Arrange
        var mockTextCompletion = this.SetupTextCompletionMock();
        var sut = new KernelBuilder().WithAIService<ITextCompletion>(null, mockTextCompletion.Object).Build();
        var semanticFunction = sut.CreateSemanticFunction("Write a simple phrase about UnitTests");

        var invoked = 0;

        sut.FunctionInvoked += (sender, e) =>
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
        mockTextCompletion.Verify(m => m.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()), Times.Exactly(pipelineCount));
    }

    [Fact]
    public async Task RunAsyncChangeVariableInvokingHandlerAsync()
    {
        var mockTextCompletion = this.SetupTextCompletionMock();
        var sut = new KernelBuilder().WithAIService<ITextCompletion>(null, mockTextCompletion.Object).Build();
        var prompt = "Write a simple phrase about UnitTests {{$input}}";
        var semanticFunction = sut.CreateSemanticFunction(prompt);

        var originalInput = "Importance";
        var newInput = "Problems";

        sut.FunctionInvoking += (sender, e) =>
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
        var mockTextCompletion = this.SetupTextCompletionMock();
        var sut = new KernelBuilder().WithAIService<ITextCompletion>(null, mockTextCompletion.Object).Build();
        var prompt = "Write a simple phrase about UnitTests {{$input}}";
        var semanticFunction = sut.CreateSemanticFunction(prompt);

        var originalInput = "Importance";
        var newInput = "Problems";

        sut.FunctionInvoked += (sender, e) =>
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

        var mockTextCompletion = this.SetupTextCompletionMock("Result3");
        var kernel = new KernelBuilder().WithAIService<ITextCompletion>(null, mockTextCompletion.Object).Build();

        var function1 = SKFunction.FromNativeMethod(Method(Function1), pluginName: PluginName);
        var function2 = SKFunction.FromNativeMethod(Method(Function2), pluginName: PluginName);

        var function3 = kernel.CreateSemanticFunction(Prompt, functionName: "Function3", pluginName: PluginName);

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
    public async Task ItUsesTextCompletionServiceWithTextPromptAsync()
    {
        // Arrange
        const string Prompt = "This is text completion prompt {{$input}}.";

        var mockTextCompletion = this.SetupTextCompletionMock("Text response from LLM.");
        var mockChatCompletion = this.SetupChatCompletionMock("Chat response from LLM.");

        var sut = new KernelBuilder()
            .WithAIService<ITextCompletion>("text-completion", mockTextCompletion.Object)
            .WithAIService<IChatCompletion>("chat-completion", mockChatCompletion.Object)
            .Build();

        var semanticFunction = sut.CreateSemanticFunction(Prompt);

        // Act
        var result = await sut.RunAsync("test", semanticFunction);

        // Assert
        Assert.Equal("Text response from LLM.", result.ToString());

        mockTextCompletion.Verify(m => m.GetCompletionsAsync(
            Prompt, It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()),
            Times.Once());

        mockChatCompletion.Verify(m => m.GetChatCompletionsAsync(
            It.IsAny<ChatHistory>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()),
            Times.Never());
    }

    [Fact]
    public async Task ItUsesChatCompletionServiceWithChatPromptAsync()
    {
        // Arrange
        const string Prompt = @"
            <message role='system'>System Message</message>
            <message role='user'>This is chat completion prompt {{$input}}.</message>
        ";

        var expectedChatHistory = new ChatHistory();
        expectedChatHistory.AddSystemMessage("System Message");
        expectedChatHistory.AddUserMessage("This is chat completion prompt {{$input}}.");

        var mockTextCompletion = this.SetupTextCompletionMock("Text response from LLM.");
        var mockChatCompletion = this.SetupChatCompletionMock("Chat response from LLM.");

        var sut = new KernelBuilder()
            .WithAIService<ITextCompletion>("text-completion", mockTextCompletion.Object)
            .WithAIService<IChatCompletion>("chat-completion", mockChatCompletion.Object)
            .Build();

        var semanticFunction = sut.CreateSemanticFunction(Prompt);

        // Act
        var result = await sut.RunAsync("test", semanticFunction);

        // Assert
        Assert.Equal("Chat response from LLM.", result.ToString());

        mockTextCompletion.Verify(m => m.GetCompletionsAsync(
            It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()),
            Times.Never());

        mockChatCompletion.Verify(m => m.GetChatCompletionsAsync(
            It.Is<ChatHistory>(actualChatHistory => this.CompareChatHistory(expectedChatHistory, actualChatHistory)),
            It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()),
            Times.Once());
    }

    private bool CompareChatHistory(ChatHistory expectedChatHistory, ChatHistory actualChatHistory)
    {
        for (var i = 0; i < expectedChatHistory.Count; i++)
        {
            if ((expectedChatHistory[i].Role != actualChatHistory[i].Role) ||
                (expectedChatHistory[i].Content != actualChatHistory[i].Content))
            {
                return false;
            }
        }

        return true;
    }

    private Mock<ITextCompletion> SetupTextCompletionMock(string? completionResult = null)
    {
        var mockTextResult = new Mock<ITextResult>();
        mockTextResult
            .Setup(m => m.GetCompletionAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(completionResult ?? "LLM Result about UnitTests");

        var mockTextCompletion = new Mock<ITextCompletion>();
        mockTextCompletion
            .Setup(m => m.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<ITextResult> { mockTextResult.Object });

        return mockTextCompletion;
    }

    private Mock<IChatCompletion> SetupChatCompletionMock(string? completionResult = null)
    {
        var mockChatResult = new Mock<IChatResult>();
        mockChatResult
            .Setup(m => m.GetChatMessageAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(new TestChatMessage(AuthorRole.Assistant, completionResult ?? "LLM Result about UnitTests"));

        var mockChatCompletion = new Mock<IChatCompletion>();
        mockChatCompletion
            .Setup(m => m.GetChatCompletionsAsync(It.IsAny<ChatHistory>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<IChatResult> { mockChatResult.Object });

        return mockChatCompletion;
    }

    private static MethodInfo Method(Delegate method)
    {
        return method.Method;
    }

    private sealed class TestChatMessage : ChatMessageBase
    {
        public TestChatMessage(AuthorRole role, string content) : base(role, content)
        {
        }
    }
}

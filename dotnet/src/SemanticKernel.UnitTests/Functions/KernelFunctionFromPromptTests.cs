// Copyright (c) Microsoft. All rights reserved.

using System;
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

public class KernelFunctionFromPromptTests
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
        var fakeTextContent = new TextContent("llmResult");

        mockTextCompletion.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { fakeTextContent });

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
        mockTextCompletion.Verify(a => a.GetTextContentsAsync("template", It.Is<OpenAIPromptExecutionSettings>(c => c.ChatSystemPrompt == expectedSystemChatPrompt), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task ItUsesServiceIdWhenProvidedAsync()
    {
        // Arrange
        var mockTextCompletion1 = new Mock<ITextCompletion>();
        var mockTextCompletion2 = new Mock<ITextCompletion>();
        var fakeTextContent = new TextContent("llmResult");

        mockTextCompletion1.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { fakeTextContent });
        mockTextCompletion2.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { fakeTextContent });

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
        mockTextCompletion1.Verify(a => a.GetTextContentsAsync("template", It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
        mockTextCompletion2.Verify(a => a.GetTextContentsAsync("template", It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Never());
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
}

// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.TemplateEngine;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;
public class MultipleModelTests
{
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
    [InlineData(new string[] { "service1" }, 1, new int[] { 1, 0, 0 })]
    [InlineData(new string[] { "service2" }, 2, new int[] { 0, 1, 0 })]
    [InlineData(new string[] { "service3" }, 0, new int[] { 0, 0, 1 })]
    [InlineData(new string[] { "service4", "service1" }, 1, new int[] { 1, 0, 0 })]
    public async Task ItUsesServiceIdByOrderAsync(string[] serviceIds, int defaultServiceIndex, int[] callCount)
    {
        // Arrange
        var mockTextCompletion1 = new Mock<ITextCompletion>();
        var mockTextCompletion2 = new Mock<ITextCompletion>();
        var mockTextCompletion3 = new Mock<ITextCompletion>();
        var mockCompletionResult = new Mock<ITextResult>();

        mockTextCompletion1.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockTextCompletion2.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockTextCompletion3.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockCompletionResult.Setup(cr => cr.GetCompletionAsync(It.IsAny<CancellationToken>())).ReturnsAsync("llmResult");

        var kernel = new KernelBuilder()
            .WithAIService("service1", mockTextCompletion1.Object, defaultServiceIndex == 0)
            .WithAIService("service2", mockTextCompletion2.Object, defaultServiceIndex == 1)
            .WithAIService("service3", mockTextCompletion3.Object, defaultServiceIndex == 2)
            .Build();

        var templateConfig = new PromptTemplateConfig();
        foreach (var serviceId in serviceIds)
        {
            templateConfig.ModelSettings.Add(new AIRequestSettings() { ServiceId = serviceId });
        }
        var func = kernel.CreateSemanticFunction("template", templateConfig, "functionName", "pluginName");

        // Act
        await kernel.RunAsync(func);

        // Assert
        mockTextCompletion1.Verify(a => a.GetCompletionsAsync("template", It.Is<AIRequestSettings>(settings => settings.ServiceId == "service1"), It.IsAny<CancellationToken>()), Times.Exactly(callCount[0]));
        mockTextCompletion2.Verify(a => a.GetCompletionsAsync("template", It.Is<AIRequestSettings>(settings => settings.ServiceId == "service2"), It.IsAny<CancellationToken>()), Times.Exactly(callCount[1]));
        mockTextCompletion3.Verify(a => a.GetCompletionsAsync("template", It.Is<AIRequestSettings>(settings => settings.ServiceId == "service3"), It.IsAny<CancellationToken>()), Times.Exactly(callCount[2]));
    }

    [Fact]
    public async Task ItUsesServiceIdWithJsonPromptTemplateConfigAsync()
    {
        // Arrange
        var mockTextCompletion1 = new Mock<ITextCompletion>();
        var mockTextCompletion2 = new Mock<ITextCompletion>();
        var mockTextCompletion3 = new Mock<ITextCompletion>();
        var mockCompletionResult = new Mock<ITextResult>();

        mockTextCompletion1.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockTextCompletion2.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockTextCompletion3.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockCompletionResult.Setup(cr => cr.GetCompletionAsync(It.IsAny<CancellationToken>())).ReturnsAsync("llmResult");

        var kernel = new KernelBuilder()
            .WithAIService("service1", mockTextCompletion1.Object, true)
            .WithAIService("service2", mockTextCompletion2.Object, false)
            .WithAIService("service3", mockTextCompletion3.Object, false)
            .Build();

        var json = @"{
  ""schema"": 1,
  ""description"": ""Semantic function"",
  ""models"": [
    {
      ""service_id"": ""service2"",
      ""max_tokens"": 100,
      ""temperature"": 0.2,
      ""top_p"": 0.0,
      ""presence_penalty"": 0.0,
      ""frequency_penalty"": 0.0,
      ""stop_sequences"": [
        ""\n""
      ]
    },
    {
      ""service_id"": ""service3"",
      ""max_tokens"": 100,
      ""temperature"": 0.4,
      ""top_p"": 0.0,
      ""presence_penalty"": 0.0,
      ""frequency_penalty"": 0.0,
      ""stop_sequences"": [
        ""\n""
      ]
    }
  ]
}";

        var templateConfig = PromptTemplateConfig.FromJson(json);
        var func = kernel.CreateSemanticFunction("template", templateConfig, "functionName", "pluginName");

        // Act
        await kernel.RunAsync(func);

        // Assert
        mockTextCompletion1.Verify(a => a.GetCompletionsAsync("template", It.Is<AIRequestSettings>(settings => settings.ServiceId == "service1"), It.IsAny<CancellationToken>()), Times.Never());
        mockTextCompletion2.Verify(a => a.GetCompletionsAsync("template", It.Is<AIRequestSettings>(settings => settings.ServiceId == "service2"), It.IsAny<CancellationToken>()), Times.Once());
        mockTextCompletion3.Verify(a => a.GetCompletionsAsync("template", It.Is<AIRequestSettings>(settings => settings.ServiceId == "service3"), It.IsAny<CancellationToken>()), Times.Never());
    }
}

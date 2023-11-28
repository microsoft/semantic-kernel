// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
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

        mockTextCompletion1.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockTextCompletion2.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockCompletionResult.Setup(cr => cr.GetCompletionAsync(It.IsAny<CancellationToken>())).ReturnsAsync("llmResult");

        var kernel = new KernelBuilder()
            .WithAIService("service1", mockTextCompletion1.Object, false)
            .WithAIService("service2", mockTextCompletion2.Object, true)
            .Build();

        var promptConfig = new PromptTemplateConfig();
        promptConfig.Template = "template";
        promptConfig.ExecutionSettings.Add(new PromptExecutionSettings() { ServiceId = "service1" });
        var func = kernel.CreateFunctionFromPrompt(promptConfig);

        // Act
        await kernel.InvokeAsync(func);

        // Assert
        mockTextCompletion1.Verify(a => a.GetCompletionsAsync("template", It.IsAny<PromptExecutionSettings>(), It.IsAny<CancellationToken>()), Times.Once());
        mockTextCompletion2.Verify(a => a.GetCompletionsAsync("template", It.IsAny<PromptExecutionSettings>(), It.IsAny<CancellationToken>()), Times.Never());
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

        var promptConfig = new PromptTemplateConfig();
        promptConfig.Template = "template";
        promptConfig.ExecutionSettings.Add(new PromptExecutionSettings() { ServiceId = "service3" });
        var func = kernel.CreateFunctionFromPrompt(promptConfig);

        // Act
        var exception = await Assert.ThrowsAsync<KernelException>(() => kernel.InvokeAsync(func));

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

        mockTextCompletion1.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockTextCompletion2.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockTextCompletion3.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockCompletionResult.Setup(cr => cr.GetCompletionAsync(It.IsAny<CancellationToken>())).ReturnsAsync("llmResult");

        var kernel = new KernelBuilder()
            .WithAIService("service1", mockTextCompletion1.Object, defaultServiceIndex == 0)
            .WithAIService("service2", mockTextCompletion2.Object, defaultServiceIndex == 1)
            .WithAIService("service3", mockTextCompletion3.Object, defaultServiceIndex == 2)
            .Build();

        var promptConfig = new PromptTemplateConfig();
        promptConfig.Template = "template";
        foreach (var serviceId in serviceIds)
        {
            promptConfig.ExecutionSettings.Add(new PromptExecutionSettings() { ServiceId = serviceId });
        }
        var func = kernel.CreateFunctionFromPrompt(promptConfig);

        // Act
        await kernel.InvokeAsync(func);

        // Assert
        mockTextCompletion1.Verify(a => a.GetCompletionsAsync("template", It.Is<PromptExecutionSettings>(settings => settings.ServiceId == "service1"), It.IsAny<CancellationToken>()), Times.Exactly(callCount[0]));
        mockTextCompletion2.Verify(a => a.GetCompletionsAsync("template", It.Is<PromptExecutionSettings>(settings => settings.ServiceId == "service2"), It.IsAny<CancellationToken>()), Times.Exactly(callCount[1]));
        mockTextCompletion3.Verify(a => a.GetCompletionsAsync("template", It.Is<PromptExecutionSettings>(settings => settings.ServiceId == "service3"), It.IsAny<CancellationToken>()), Times.Exactly(callCount[2]));
    }

    [Fact]
    public async Task ItUsesServiceIdWithJsonPromptTemplateConfigAsync()
    {
        // Arrange
        var mockTextCompletion1 = new Mock<ITextCompletion>();
        var mockTextCompletion2 = new Mock<ITextCompletion>();
        var mockTextCompletion3 = new Mock<ITextCompletion>();
        var mockCompletionResult = new Mock<ITextResult>();

        mockTextCompletion1.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockTextCompletion2.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockTextCompletion3.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockCompletionResult.Setup(cr => cr.GetCompletionAsync(It.IsAny<CancellationToken>())).ReturnsAsync("llmResult");

        var kernel = new KernelBuilder()
            .WithAIService("service1", mockTextCompletion1.Object, true)
            .WithAIService("service2", mockTextCompletion2.Object, false)
            .WithAIService("service3", mockTextCompletion3.Object, false)
            .Build();

        var json = @"{
  ""template"": ""template"",
  ""description"": ""Semantic function"",
  ""execution_settings"": [
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

        var promptConfig = PromptTemplateConfig.FromJson(json);
        var func = kernel.CreateFunctionFromPrompt(promptConfig);

        // Act
        await kernel.InvokeAsync(func);

        // Assert
        mockTextCompletion1.Verify(a => a.GetCompletionsAsync("template", It.Is<PromptExecutionSettings>(settings => settings.ServiceId == "service1"), It.IsAny<CancellationToken>()), Times.Never());
        mockTextCompletion2.Verify(a => a.GetCompletionsAsync("template", It.Is<PromptExecutionSettings>(settings => settings.ServiceId == "service2"), It.IsAny<CancellationToken>()), Times.Once());
        mockTextCompletion3.Verify(a => a.GetCompletionsAsync("template", It.Is<PromptExecutionSettings>(settings => settings.ServiceId == "service3"), It.IsAny<CancellationToken>()), Times.Never());
    }
}

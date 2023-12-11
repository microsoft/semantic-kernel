// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TextGeneration;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class MultipleModelTests
{
    [Fact]
    public async Task ItUsesServiceIdWhenProvidedAsync()
    {
        // Arrange
        var mockTextGeneration1 = new Mock<ITextGenerationService>();
        var mockTextGeneration2 = new Mock<ITextGenerationService>();

        var fakeTextContent = new TextContent("llmResult");
        mockTextGeneration1.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { fakeTextContent });
        mockTextGeneration2.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { fakeTextContent });

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton("service1", mockTextGeneration1.Object);
        builder.Services.AddKeyedSingleton("service2", mockTextGeneration2.Object);
        Kernel kernel = builder.Build();

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

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton("service1", mockTextGeneration1.Object);
        builder.Services.AddKeyedSingleton("service2", mockTextGeneration2.Object);
        Kernel kernel = builder.Build();

        var promptConfig = new PromptTemplateConfig();
        promptConfig.Template = "template";
        promptConfig.ExecutionSettings.Add(new PromptExecutionSettings() { ServiceId = "service3" });
        var func = kernel.CreateFunctionFromPrompt(promptConfig);

        // Act
        var exception = await Assert.ThrowsAsync<KernelException>(() => kernel.InvokeAsync(func));

        // Assert
        Assert.Equal("Required service of type Microsoft.SemanticKernel.TextGeneration.ITextGenerationService not registered. Expected serviceIds: service3.", exception.Message);
    }

    [Theory]
    [InlineData(new string[] { "service1" }, new int[] { 1, 0, 0 })]
    [InlineData(new string[] { "service4", "service1" }, new int[] { 1, 0, 0 })]
    public async Task ItUsesServiceIdByOrderAsync(string[] serviceIds, int[] callCount)
    {
        // Arrange
        var mockTextGeneration1 = new Mock<ITextGenerationService>();
        var mockTextGeneration2 = new Mock<ITextGenerationService>();
        var mockTextGeneration3 = new Mock<ITextGenerationService>();
        var fakeTextContent = new TextContent("llmResult");

        mockTextGeneration1.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { fakeTextContent });
        mockTextGeneration2.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { fakeTextContent });
        mockTextGeneration3.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { fakeTextContent });

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton("service1", mockTextGeneration1.Object);
        builder.Services.AddKeyedSingleton("service2", mockTextGeneration2.Object);
        builder.Services.AddKeyedSingleton("service3", mockTextGeneration3.Object);
        Kernel kernel = builder.Build();

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
        mockTextGeneration1.Verify(a => a.GetTextContentsAsync("template", It.Is<PromptExecutionSettings>(settings => settings.ServiceId == "service1"), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Exactly(callCount[0]));
        mockTextGeneration2.Verify(a => a.GetTextContentsAsync("template", It.Is<PromptExecutionSettings>(settings => settings.ServiceId == "service2"), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Exactly(callCount[1]));
        mockTextGeneration3.Verify(a => a.GetTextContentsAsync("template", It.Is<PromptExecutionSettings>(settings => settings.ServiceId == "service3"), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Exactly(callCount[2]));
    }

    [Fact]
    public async Task ItUsesServiceIdWithJsonPromptTemplateConfigAsync()
    {
        // Arrange
        var mockTextGeneration1 = new Mock<ITextGenerationService>();
        var mockTextGeneration2 = new Mock<ITextGenerationService>();
        var mockTextGeneration3 = new Mock<ITextGenerationService>();
        var fakeTextContent = new TextContent("llmResult");

        mockTextGeneration1.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { fakeTextContent });
        mockTextGeneration2.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { fakeTextContent });
        mockTextGeneration3.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { fakeTextContent });

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton("service1", mockTextGeneration1.Object);
        builder.Services.AddKeyedSingleton("service2", mockTextGeneration2.Object);
        builder.Services.AddKeyedSingleton("service3", mockTextGeneration3.Object);
        Kernel kernel = builder.Build();

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
        mockTextGeneration1.Verify(a => a.GetTextContentsAsync("template", It.Is<PromptExecutionSettings>(settings => settings.ServiceId == "service1"), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Never());
        mockTextGeneration2.Verify(a => a.GetTextContentsAsync("template", It.Is<PromptExecutionSettings>(settings => settings.ServiceId == "service2"), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
        mockTextGeneration3.Verify(a => a.GetTextContentsAsync("template", It.Is<PromptExecutionSettings>(settings => settings.ServiceId == "service3"), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Never());
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.TemplateEngine;
using Moq;
using Xunit;
using static Microsoft.SemanticKernel.SemanticFunctions.PromptConfig;

namespace SemanticKernel.UnitTests.SkillDefinition;

public sealed class SKFunctionTests1
{
    private readonly Mock<IPromptTemplateEngine> _templateEngine;

    public SKFunctionTests1()
    {
        this._templateEngine = new Mock<IPromptTemplateEngine>();
        this._templateEngine.Setup(x => x.RenderAsync(It.IsAny<string>(), It.IsAny<SKContext>(), It.IsAny<CancellationToken>())).ReturnsAsync("foo");
    }

    [Fact]
    public void ItHasDefaultRequestSettings()
    {
        // Arrange
        var promptConfig = new PromptConfig()
        {
            PluginName = "sk",
            FunctionName = "name",
            Template = "Say hello in German",
        };

        // Act
        var skFunction = SKFunction.FromPromptConfig(promptConfig, this._templateEngine.Object);

        // Assert
        Assert.Equal(0, skFunction.RequestSettings.Temperature);
        Assert.Equal(null, skFunction.RequestSettings.MaxTokens);
    }

    [Fact]
    public void ItAllowsToUpdateRequestSettings()
    {
        // Arrange
        var settings = new CompleteRequestSettings
        {
            Temperature = 0.9,
            MaxTokens = 2001,
        };
        var promptRequestSettings = new PromptRequestSettings();
        promptRequestSettings.Properties["temperature"] = 0.9;
        promptRequestSettings.Properties["max_tokens"] = 2001;
        var promptConfig = new PromptConfig()
        {
            Description = "Say hello in German",
            InputParameters = new(),
            PluginName = "SpeakGermanPlugin",
            FunctionName = "SayHello",
            Template = "Say hello in German",
            RequestSettings = new List<PromptRequestSettings>() { promptRequestSettings },
        };
        var skFunction = SKFunction.FromPromptConfig(promptConfig, this._templateEngine.Object);

        // Act
        skFunction.RequestSettings.Temperature = 1.3;
        skFunction.RequestSettings.MaxTokens = 130;

        // Assert
        Assert.Equal(1.3, skFunction.RequestSettings.Temperature);
        Assert.Equal(130, skFunction.RequestSettings.MaxTokens);

        // Act
        skFunction.RequestSettings.Temperature = 0.7;

        // Assert
        Assert.Equal(0.7, skFunction.RequestSettings.Temperature);

        // Act
        skFunction.SetAIConfiguration(settings);

        // Assert
        Assert.Equal(settings.Temperature, skFunction.RequestSettings.Temperature);
        Assert.Equal(settings.MaxTokens, skFunction.RequestSettings.MaxTokens);
    }

    private static Mock<IPromptTemplate> MockPromptTemplate()
    {
        var promptTemplate = new Mock<IPromptTemplate>();

        promptTemplate.Setup(x => x.RenderAsync(It.IsAny<SKContext>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync("some prompt");

        promptTemplate
            .Setup(x => x.GetParameters())
            .Returns(new List<ParameterView>());

        return promptTemplate;
    }

    private static Mock<ITextCompletion> MockAIService(string result)
    {
        var aiService = new Mock<ITextCompletion>();
        var textCompletionResult = new Mock<ITextResult>();

        textCompletionResult
            .Setup(x => x.GetCompletionAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(result);

        aiService
            .Setup(x => x.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<ITextResult> { textCompletionResult.Object });

        return aiService;
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.SkillDefinition;

public sealed class SKFunctionTests1
{
    private readonly Mock<IPromptTemplate> _promptTemplate;

    public SKFunctionTests1()
    {
        this._promptTemplate = new Mock<IPromptTemplate>();
        this._promptTemplate.Setup(x => x.RenderAsync(It.IsAny<SKContext>(), It.IsAny<CancellationToken>())).ReturnsAsync("foo");
        this._promptTemplate.Setup(x => x.GetParameters()).Returns(new List<ParameterView>());
    }

    [Fact]
    public void ItHasDefaultRequestSettings()
    {
        // Arrange
        var templateConfig = new PromptTemplateConfig();
        var functionConfig = new SemanticFunctionConfig(templateConfig, this._promptTemplate.Object);

        // Act
        var skFunction = SKFunction.FromSemanticConfig("sk", "name", functionConfig);

        // Assert
        Assert.Null(skFunction.RequestSettings);
    }

    [Fact]
    public void ItAllowsToUpdateRequestSettings()
    {
        // Arrange
        var requestSettings = new AIRequestSettings()
        {
            ServiceId = "service",
            ExtensionData = new Dictionary<string, object>()
            {
                { "MaxTokens", 1024 },
            }
        };
        var templateConfig = new PromptTemplateConfig()
        {
            Completion = requestSettings
        };
        var functionConfig = new SemanticFunctionConfig(templateConfig, this._promptTemplate.Object);
        var skFunction = SKFunction.FromSemanticConfig("sk", "name", functionConfig);

        // Act
        requestSettings.ServiceId = "service1";
        requestSettings.ExtensionData["MaxTokens"] = 130;

        // Assert
        Assert.Equal("service1", skFunction.RequestSettings?.ServiceId);
        Assert.Equal(130, skFunction.RequestSettings?.ExtensionData?["MaxTokens"]);

        // Act
        requestSettings.ExtensionData["Temperature"] = 0.7;

        // Assert
        Assert.Equal(0.7, skFunction.RequestSettings?.ExtensionData?["Temperature"]);

        // Act
        skFunction.SetAIConfiguration(requestSettings);

        // Assert
        Assert.Equal("service1", skFunction.RequestSettings?.ServiceId);
        Assert.Equal(130, skFunction.RequestSettings?.ExtensionData?["MaxTokens"]);
        Assert.Equal(0.7, skFunction.RequestSettings?.ExtensionData?["Temperature"]);
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
            .Setup(x => x.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<ITextResult> { textCompletionResult.Object });

        return aiService;
    }
}

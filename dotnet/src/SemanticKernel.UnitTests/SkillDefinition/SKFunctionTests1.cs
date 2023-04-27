// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Security;
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
        this._promptTemplate.Setup(x => x.RenderAsync(It.IsAny<SKContext>())).ReturnsAsync("foo");
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
        Assert.Equal(0, skFunction.RequestSettings.Temperature);
        Assert.Equal(256, skFunction.RequestSettings.MaxTokens);
    }

    [Fact]
    public void ItHasDefaultTrustSettings()
    {
        // Arrange
        var templateConfig = new PromptTemplateConfig();
        var functionConfig = new SemanticFunctionConfig(templateConfig, this._promptTemplate.Object);

        // Act
        var skFunction = SKFunction.FromSemanticConfig("sk", "name", functionConfig);

        // Assert
        Assert.False(skFunction.IsSensitive);
        Assert.IsType<TrustService>(skFunction.TrustServiceInstance);
    }

    [Fact]
    public void ItAllowsToUpdateRequestSettings()
    {
        // Arrange
        var templateConfig = new PromptTemplateConfig();
        var functionConfig = new SemanticFunctionConfig(templateConfig, this._promptTemplate.Object);
        var skFunction = SKFunction.FromSemanticConfig("sk", "name", functionConfig);
        var settings = new CompleteRequestSettings
        {
            Temperature = 0.9,
            MaxTokens = 2001,
        };

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

    [Fact]
    public void ItAllowsFunctionToBeSensitive()
    {
        // Arrange
        var templateConfig = new PromptTemplateConfig { IsSensitive = true };
        var functionConfig = new SemanticFunctionConfig(templateConfig, this._promptTemplate.Object);
        var skFunction = SKFunction.FromSemanticConfig("sk", "name", functionConfig);

        // Assert
        Assert.True(functionConfig.PromptTemplateConfig.IsSensitive);
        Assert.True(skFunction.IsSensitive);
    }

    [Fact]
    public void ItCanSetCustomTrustService()
    {
        // Arrange
        var templateConfig = new PromptTemplateConfig();
        var functionConfig = new SemanticFunctionConfig(templateConfig, this._promptTemplate.Object);
        var trustService = new CustomTrustService();

        // Act
        var skFunction = SKFunction.FromSemanticConfig("sk", "name", functionConfig, trustService: trustService);

        // Assert
        Assert.IsType<CustomTrustService>(skFunction.TrustServiceInstance);
        Assert.Equal(trustService, skFunction.TrustServiceInstance);
    }

    private sealed class CustomTrustService : ITrustService
    {
        public Task<bool> ValidateContextAsync(ISKFunction func, SKContext context)
        {
            return Task.FromResult(context.IsTrusted);
        }

        public Task<TrustAwareString> ValidatePromptAsync(ISKFunction func, SKContext context, string prompt)
        {
            return Task.FromResult(new TrustAwareString(prompt, context.IsTrusted));
        }
    }
}

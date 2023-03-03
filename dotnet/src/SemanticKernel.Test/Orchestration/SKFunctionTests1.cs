// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using SemanticKernelTests.XunitHelpers;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernelTests.Orchestration;

public sealed class SKFunctionTests1 : IDisposable
{
    private readonly RedirectOutput _testOutputHelper;
    private readonly Mock<IPromptTemplate> _promptTemplate;

    public SKFunctionTests1(ITestOutputHelper testOutputHelper)
    {
        this._testOutputHelper = new RedirectOutput(testOutputHelper);
        Console.SetOut(this._testOutputHelper);

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
        Assert.Equal(100, skFunction.RequestSettings.MaxTokens);
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

    public void Dispose()
    {
        this._testOutputHelper.Dispose();
    }
}

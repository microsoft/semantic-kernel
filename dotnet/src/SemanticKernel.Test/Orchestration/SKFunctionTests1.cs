// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Diagnostics;
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
        Verify.NotNull(skFunction.RequestSettings.CompleteRequestSettings, "Completion request settings cannot be empty");
        Assert.Equal(0, skFunction.RequestSettings.CompleteRequestSettings.Temperature);
        Assert.Equal(100, skFunction.RequestSettings.CompleteRequestSettings.MaxTokens);
    }

    [Fact]
    public void ItAllowsToUpdateRequestSettings()
    {
        // Arrange
        var templateConfig = new PromptTemplateConfig();
        var functionConfig = new SemanticFunctionConfig(templateConfig, this._promptTemplate.Object);
        var skFunction = SKFunction.FromSemanticConfig("sk", "name", functionConfig);
        Verify.NotNull(skFunction.RequestSettings.CompleteRequestSettings, "Completion request settings cannot be empty");

        var settings = new RequestSettings
        {
            CompleteRequestSettings = new CompleteRequestSettings
            {
                Temperature = 0.9,
                MaxTokens = 2001,
            }
        };

        // Act
        skFunction.RequestSettings.CompleteRequestSettings.Temperature = 1.3;
        skFunction.RequestSettings.CompleteRequestSettings.MaxTokens = 130;

        // Assert
        Assert.Equal(1.3, skFunction.RequestSettings.CompleteRequestSettings.Temperature);
        Assert.Equal(130, skFunction.RequestSettings.CompleteRequestSettings.MaxTokens);

        // Act
        skFunction.RequestSettings.CompleteRequestSettings.Temperature = 0.7;

        // Assert
        Assert.Equal(0.7, skFunction.RequestSettings.CompleteRequestSettings.Temperature);

        // Act
        skFunction.SetAIConfiguration(settings);

        // Assert
        Assert.Equal(settings.CompleteRequestSettings.Temperature, skFunction.RequestSettings.CompleteRequestSettings.Temperature);
        Assert.Equal(settings.CompleteRequestSettings.MaxTokens, skFunction.RequestSettings.CompleteRequestSettings.MaxTokens);
    }

    public void Dispose()
    {
        this._testOutputHelper.Dispose();
    }
}

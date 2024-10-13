// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using System.Text.Json.Nodes;
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
    public void ItAllowsToUpdateServiceSettings()
    {
        // Arrange
        var templateConfig = new PromptTemplateConfig();
        var functionConfig = new SemanticFunctionConfig(templateConfig, this._promptTemplate.Object);
        var skFunction = SKFunction.FromSemanticConfig("sk", "name", functionConfig);
        var settings = new JsonObject
        {
            ["temperature"] = 0.9,
            ["max_tokens"] = 2001,
        };

        // Act
        skFunction.ServiceSettings["temperature"] = 1.3;
        skFunction.ServiceSettings["max_tokens"] = 130;

        // Assert
        Assert.Equal(1.3, skFunction.ServiceSettings["temperature"]?.GetValue<double>());
        Assert.Equal(130, skFunction.ServiceSettings["max_tokens"]?.GetValue<int>());

        // Act
        skFunction.ServiceSettings["temperature"] = 0.7;

        // Assert
        Assert.Equal(0.7, skFunction.ServiceSettings["temperature"]?.GetValue<double>());

        // Act
        skFunction.SetAIConfiguration(settings);

        // Assert
        Assert.Equal(settings["temperature"], skFunction.ServiceSettings["temperature"]);
        Assert.Equal(settings["max_tokens"], skFunction.ServiceSettings["max_tokens"]);
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
        var trustService = new CustomTrustService(false, false);

        // Act
        var skFunction = SKFunction.FromSemanticConfig("sk", "name", functionConfig, trustService: trustService);

        // Assert
        Assert.IsType<CustomTrustService>(skFunction.TrustServiceInstance);
        Assert.Equal(trustService, skFunction.TrustServiceInstance);
    }

    [Fact]
    public async Task SemanticFunctionWithValidateContextFalseShouldTagResultAsUntrusted()
    {
        // Arrange
        var expectedResultString = "some result";
        var trustService = new CustomTrustService(false, true);
        var promptTemplateConfig = new PromptTemplateConfig { IsSensitive = true };
        var promptTemplate = MockPromptTemplate();
        var functionConfig = new SemanticFunctionConfig(promptTemplateConfig, promptTemplate.Object);
        var func = SKFunction.FromSemanticConfig(
            "exampleSkill",
            "exampleFunction",
            functionConfig,
            trustService
        );
        var aiService = MockAIService(expectedResultString);

        // Act
        var result = await func.InvokeAsync(textCompletionService: aiService.Object);

        // Assert
        // Since CustomTrustService will return false for ValidateContext, the result should be tagged as untrusted
        Assert.Equal(expectedResultString, result.Result);
        Assert.False(result.Variables.Input.IsTrusted);
        Assert.False(result.IsTrusted);
    }

    [Fact]
    public async Task SemanticFunctionWithValidatePromptFalseShouldTagResultAsUntrusted()
    {
        // Arrange
        var expectedResultString = "some result";
        var trustService = new CustomTrustService(true, false);
        var promptTemplateConfig = new PromptTemplateConfig { IsSensitive = true };
        var promptTemplate = MockPromptTemplate();
        var functionConfig = new SemanticFunctionConfig(promptTemplateConfig, promptTemplate.Object);
        var func = SKFunction.FromSemanticConfig(
            "exampleSkill",
            "exampleFunction",
            functionConfig,
            trustService
        );
        var aiService = MockAIService(expectedResultString);

        // Act
        var result = await func.InvokeAsync(textCompletionService: aiService.Object);

        // Assert
        // Since CustomTrustService will return false for ValidatePrompt, the result should be tagged as untrusted
        Assert.Equal(expectedResultString, result.Result);
        Assert.False(result.Variables.Input.IsTrusted);
        Assert.False(result.IsTrusted);
    }

    [Fact]
    public async Task SemanticFunctionWithValidateContentAndPromptTrueShouldKeepResultTrusted()
    {
        // Arrange
        var expectedResultString = "some result";
        var trustService = new CustomTrustService(true, true);
        var promptTemplateConfig = new PromptTemplateConfig { IsSensitive = true };
        var promptTemplate = MockPromptTemplate();
        var functionConfig = new SemanticFunctionConfig(promptTemplateConfig, promptTemplate.Object);
        var func = SKFunction.FromSemanticConfig(
            "exampleSkill",
            "exampleFunction",
            functionConfig,
            trustService
        );
        var aiService = MockAIService(expectedResultString);

        // Act
        var result = await func.InvokeAsync(textCompletionService: aiService.Object);

        // Assert
        // Since CustomTrustService will return true for ValidateContext/ValidatePrompt,
        // the result should be kept trusted
        Assert.Equal(expectedResultString, result.Result);
        Assert.True(result.Variables.Input.IsTrusted);
        Assert.True(result.IsTrusted);
    }

    private static Mock<IPromptTemplate> MockPromptTemplate()
    {
        var promptTemplate = new Mock<IPromptTemplate>();

        promptTemplate.Setup(x => x.RenderAsync(It.IsAny<SKContext>()))
            .ReturnsAsync("some prompt");

        promptTemplate
            .Setup(x => x.GetParameters())
            .Returns(new List<ParameterView>()); ;

        return promptTemplate;
    }

    private static Mock<ITextCompletion> MockAIService(string result)
    {
        var aiService = new Mock<ITextCompletion>();
        var textCompletionResult = new Mock<ITextCompletionResult>();

        textCompletionResult
            .Setup(x => x.GetCompletionAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(result);

        aiService
            .Setup(x => x.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<ITextCompletionResult> { textCompletionResult.Object });

        return aiService;
    }

    private sealed class CustomTrustService : ITrustService
    {
        private bool _validateContextResult;
        private bool _validatePromptResult;

        public CustomTrustService(bool validateContextResult, bool validatePromptResult)
        {
            this._validateContextResult = validateContextResult;
            this._validatePromptResult = validatePromptResult;
        }

        public Task<bool> ValidateContextAsync(ISKFunction func, SKContext context)
        {
            return Task.FromResult(this._validateContextResult);
        }

        public Task<TrustAwareString> ValidatePromptAsync(ISKFunction func, SKContext context, string prompt)
        {
            return Task.FromResult(new TrustAwareString(prompt, this._validatePromptResult));
        }
    }
}

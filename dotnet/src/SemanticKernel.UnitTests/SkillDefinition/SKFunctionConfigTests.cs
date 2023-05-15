// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.SkillDefinition;

public class SKFunctionConfigTests
{
    private const string SkillName = "TestSkill";

    [Fact]
    public async Task ItUsesDefaultSettingsWhenRecommendedServicesMissedAsync()
    {
        // Arrange
        var mockCompletionService = new Mock<ITextCompletion>();
        var expectedSettings = new JsonObject
        {
            ["max_tokens"] = 60,
            ["temperature"] = 0.5,
            ["top_p"] = 0.3,
            ["presence_penalty"] = 0.2,
            ["frequency_penalty"] = 0.1,
            ["stop_sequences"] = new JsonArray { "test_stop_sequence" }
        };

        var kernel = this.GetKernelWithSkills(mockCompletionService.Object);
        var function = kernel.Func(SkillName, "WithDefaultSettings");

        // Act
        var result = await kernel.RunAsync(function);

        // Assert
        mockCompletionService.Verify(x => x.CompleteAsync(
            It.IsAny<string>(),
            It.Is<JsonObject>(settings => this.AssertCompletionSettingsEqual(expectedSettings, settings)),
            It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Fact]
    public async Task ItUsesFirstRecommendedServiceSettingsAsync()
    {
        // Arrange
        var mockCompletionService = new Mock<ITextCompletion>();
        var expectedSettings = new JsonObject
        {
            ["max_tokens"] = 1000,
            ["temperature"] = 0.9,
            ["top_p"] = 0.1,
            ["presence_penalty"] = 0.2,
            ["frequency_penalty"] = 0.3,
            ["stop_sequences"] = new JsonArray { "test_stop_sequence" }
        };

        var kernel = this.GetKernelWithSkills(mockCompletionService.Object, "text-davinci-003");
        var function = kernel.Func(SkillName, "WithServices");

        // Act
        var result = await kernel.RunAsync(function);

        // Assert
        mockCompletionService.Verify(x => x.CompleteAsync(
            It.IsAny<string>(),
            It.Is<JsonObject>(settings => this.AssertCompletionSettingsEqual(expectedSettings, settings)),
            It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Fact]
    public async Task ItUsesRegisteredRecommendedServiceSettingsAsync()
    {
        // Arrange
        var mockCompletionService = new Mock<ITextCompletion>();
        var expectedSettings = new JsonObject
        {
            ["n"] = 1,
            ["size"] = "1024x1024"
        };

        var kernel = this.GetKernelWithSkills(mockCompletionService.Object, "dalle");
        var function = kernel.Func(SkillName, "WithServices");

        // Act
        var result = await kernel.RunAsync(function);

        // Assert
        mockCompletionService.Verify(x => x.CompleteAsync(
            It.IsAny<string>(),
            It.Is<JsonObject>(settings => this.AssertImageGenerationSettingsEqual(expectedSettings, settings)),
            It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("random-service")]
    public async Task ItUsesDefaultSettingsWhenRecommendedServiceIsNotRegisteredInKernelAsync(string? serviceId)
    {
        // Arrange
        var mockCompletionService = new Mock<ITextCompletion>();
        var expectedSettings = new JsonObject
        {
            ["max_tokens"] = 60,
            ["temperature"] = 0.5,
            ["top_p"] = 0.3,
            ["presence_penalty"] = 0.2,
            ["frequency_penalty"] = 0.1,
            ["stop_sequences"] = new JsonArray { "test_stop_sequence" }
        };

        var kernel = this.GetKernelWithSkills(mockCompletionService.Object, serviceId);
        var function = kernel.Func(SkillName, "WithServices");

        // Act
        var result = await kernel.RunAsync(function);

        // Assert
        mockCompletionService.Verify(x => x.CompleteAsync(
            It.IsAny<string>(),
            It.Is<JsonObject>(settings => this.AssertCompletionSettingsEqual(expectedSettings, settings)),
            It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Fact]
    public async Task ItUsesFunctionConfigurationUpdatedInRuntimeAsync()
    {
        // Arrange
        var mockCompletionService = new Mock<ITextCompletion>();
        var expectedSettings = new JsonObject
        {
            ["max_tokens"] = 123,
            ["temperature"] = 0.9,
            ["top_p"] = 0.5,
            ["presence_penalty"] = 0.4,
            ["frequency_penalty"] = 0.3,
            ["stop_sequences"] = new JsonArray { "new_stop_sequence" }
        };

        var kernel = this.GetKernel(mockCompletionService.Object);
        var function = kernel.CreateSemanticFunction(
            promptTemplate: "test prompt",
            functionName: "TestFunction",
            skillName: "TestSkill",
            description: "test description",
            maxTokens: 256,
            temperature: 0.9,
            topP: 0.5,
            presencePenalty: 0.4,
            frequencyPenalty: 0.3,
            stopSequences: new List<string> { "new_stop_sequence" });

        // Act
        function.ServiceSettings["max_tokens"] = 123;

        var result = await kernel.RunAsync(function);

        // Assert
        mockCompletionService.Verify(x => x.CompleteAsync(
            It.IsAny<string>(),
            It.Is<JsonObject>(settings => this.AssertCompletionSettingsEqual(expectedSettings, settings)),
            It.IsAny<CancellationToken>()),
            Times.Once);
    }

    #region private ================================================================================

    private IKernel GetKernel(ITextCompletion completionService, string? serviceId = null)
    {
        var kernel = Kernel.Builder
            .Configure(c =>
            {
                c.AddTextCompletionService((_) => completionService, serviceId);
            })
            .Build();

        return kernel;
    }

    private IKernel GetKernelWithSkills(ITextCompletion completionService, string? serviceId = null)
    {
        var kernel = this.GetKernel(completionService, serviceId);

        kernel.ImportSemanticSkillFromDirectory(this.GetParentFolder(), SkillName);

        return kernel;
    }

    private string GetParentFolder()
    {
        return Path.Join(this.GetRootPath(), "TestData", "skills");
    }

    private string GetRootPath()
    {
        return Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location)!;
    }

    private bool AssertCompletionSettingsEqual(JsonObject expected, JsonObject actual)
    {
        var expectedSettings = expected.Deserialize<TextCompletionSettings>();
        var actualSettings = actual.Deserialize<TextCompletionSettings>();

        Assert.NotNull(expectedSettings);
        Assert.NotNull(actualSettings);

        Assert.Equal(expectedSettings.MaxTokens, actualSettings.MaxTokens);
        Assert.Equal(expectedSettings.Temperature, actualSettings.Temperature);
        Assert.Equal(expectedSettings.TopP, actualSettings.TopP);
        Assert.Equal(expectedSettings.PresencePenalty, actualSettings.PresencePenalty);
        Assert.Equal(expectedSettings.FrequencyPenalty, actualSettings.FrequencyPenalty);
        Assert.Equal(expectedSettings.StopSequences, actualSettings.StopSequences);

        return true;
    }

    private bool AssertImageGenerationSettingsEqual(JsonObject expected, JsonObject actual)
    {
        var expectedSettings = expected.Deserialize<ImageGenerationSettings>();
        var actualSettings = actual.Deserialize<ImageGenerationSettings>();

        Assert.NotNull(expectedSettings);
        Assert.NotNull(actualSettings);

        Assert.Equal(expectedSettings.Amount, actualSettings.Amount);
        Assert.Equal(expectedSettings.Size, actualSettings.Size);

        return true;
    }

#pragma warning disable CA1812 // remove class never instantiated (used by System.Text.Json)

    private sealed class TextCompletionSettings
    {
        [JsonPropertyName("temperature")]
        public double Temperature { get; set; }

        [JsonPropertyName("top_p")]
        public double TopP { get; set; }

        [JsonPropertyName("presence_penalty")]
        public double PresencePenalty { get; set; }

        [JsonPropertyName("frequency_penalty")]
        public double FrequencyPenalty { get; set; }

        [JsonPropertyName("max_tokens")]
        public int MaxTokens { get; set; }

        [JsonPropertyName("stop_sequences")]
        public IList<string>? StopSequences { get; set; }
    }

    private sealed class ImageGenerationSettings
    {
        [JsonPropertyName("n")]
        public int Amount { get; set; }

        [JsonPropertyName("size")]
        public string? Size { get; set; }
    }

#pragma warning restore CA1812 // Avoid uninstantiated internal classes

    #endregion
}

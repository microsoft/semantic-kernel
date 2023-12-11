// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class OrderedAIServiceSelectorTests
{
    [Fact]
    public void ItThrowsAnSKExceptionForNoServices()
    {
        // Arrange
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromPrompt("Hello AI");
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        // Assert
        Assert.Throws<KernelException>(() => serviceSelector.SelectAIService<ITextGenerationService>(kernel, function, new KernelArguments()));
    }

    [Fact]
    public void ItGetsAIServiceConfigurationForSingleAIService()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton<IAIService>("service1", new AIService());
        Kernel kernel = builder.Build();

        var function = kernel.CreateFunctionFromPrompt("Hello AI");
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultExecutionSettings) = serviceSelector.SelectAIService<IAIService>(kernel, function, new KernelArguments());

        // Assert
        Assert.NotNull(aiService);
        Assert.Null(defaultExecutionSettings);
    }

    [Fact]
    public void ItGetsAIServiceConfigurationForSingleTextGeneration()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", new TextGenerationService("model_id_1"));
        Kernel kernel = builder.Build();

        var function = kernel.CreateFunctionFromPrompt("Hello AI");
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultExecutionSettings) = serviceSelector.SelectAIService<ITextGenerationService>(kernel, function, new KernelArguments());

        // Assert
        Assert.NotNull(aiService);
        Assert.Null(defaultExecutionSettings);
    }

    [Fact]
    public void ItGetsAIServiceConfigurationForTextGenerationByServiceId()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", new TextGenerationService("model_id_1"));
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service2", new TextGenerationService("model_id_2"));
        Kernel kernel = builder.Build();

        var executionSettings = new PromptExecutionSettings() { ServiceId = "service2" };
        var function = kernel.CreateFunctionFromPrompt("Hello AI", executionSettings);
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultExecutionSettings) = serviceSelector.SelectAIService<ITextGenerationService>(kernel, function, new KernelArguments());

        // Assert
        Assert.Equal(kernel.GetRequiredService<ITextGenerationService>("service2"), aiService);
        Assert.Equal(executionSettings, defaultExecutionSettings);
    }

    [Fact]
    public void ItThrowsAnSKExceptionForNotFoundService()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", new TextGenerationService("model_id_1"));
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service2", new TextGenerationService("model_id_2"));
        Kernel kernel = builder.Build();

        var executionSettings = new PromptExecutionSettings() { ServiceId = "service3" };
        var function = kernel.CreateFunctionFromPrompt("Hello AI", executionSettings);
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        // Assert
        Assert.Throws<KernelException>(() => serviceSelector.SelectAIService<ITextGenerationService>(kernel, function, new KernelArguments()));
    }

    [Fact]
    public void ItUsesDefaultServiceForNoExecutionSettings()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", new TextGenerationService("model_id_1"));
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service2", new TextGenerationService("model_id_2"));
        Kernel kernel = builder.Build();
        var function = kernel.CreateFunctionFromPrompt("Hello AI");
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultExecutionSettings) = serviceSelector.SelectAIService<ITextGenerationService>(kernel, function, new KernelArguments());

        // Assert
        Assert.Equal(kernel.GetRequiredService<ITextGenerationService>("service2"), aiService);
        Assert.Null(defaultExecutionSettings);
    }

    [Fact]
    public void ItUsesDefaultServiceAndSettingsForDefaultExecutionSettings()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", new TextGenerationService("model_id_1"));
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service2", new TextGenerationService("model_id_2"));
        Kernel kernel = builder.Build();

        var executionSettings = new PromptExecutionSettings();
        var function = kernel.CreateFunctionFromPrompt("Hello AI", executionSettings);
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultExecutionSettings) = serviceSelector.SelectAIService<ITextGenerationService>(kernel, function, new KernelArguments());

        // Assert
        Assert.Equal(kernel.GetRequiredService<ITextGenerationService>("service2"), aiService);
        Assert.Equal(executionSettings, defaultExecutionSettings);
    }

    [Fact]
    public void ItUsesDefaultServiceAndSettingsEmptyServiceId()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", new TextGenerationService("model_id_1"));
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service2", new TextGenerationService("model_id_2"));
        Kernel kernel = builder.Build();

        var executionSettings = new PromptExecutionSettings() { ServiceId = "" };
        var function = kernel.CreateFunctionFromPrompt("Hello AI", executionSettings);
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultExecutionSettings) = serviceSelector.SelectAIService<ITextGenerationService>(kernel, function, new KernelArguments());

        // Assert
        Assert.Equal(kernel.GetRequiredService<ITextGenerationService>("service2"), aiService);
        Assert.Equal(executionSettings, defaultExecutionSettings);
    }

    [Theory]
    [InlineData(new string[] { "service1" }, "service1")]
    [InlineData(new string[] { "service2" }, "service2")]
    [InlineData(new string[] { "service3" }, "service3")]
    [InlineData(new string[] { "service4", "service1" }, "service1")]
    [InlineData(new string[] { "service4", "" }, "service3")]
    public void ItGetsAIServiceConfigurationByOrder(string[] serviceIds, string expectedServiceId)
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", new TextGenerationService("model_id_1"));
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service2", new TextGenerationService("model_id_2"));
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service3", new TextGenerationService("model_id_3"));
        Kernel kernel = builder.Build();

        var executionSettings = new List<PromptExecutionSettings>();
        foreach (var serviceId in serviceIds)
        {
            executionSettings.Add(new PromptExecutionSettings() { ServiceId = serviceId });
        }
        var function = kernel.CreateFunctionFromPrompt(promptConfig: new PromptTemplateConfig() { Template = "Hello AI", ExecutionSettings = executionSettings });
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultExecutionSettings) = serviceSelector.SelectAIService<ITextGenerationService>(kernel, function, new KernelArguments());

        // Assert
        Assert.Equal(kernel.GetRequiredService<ITextGenerationService>(expectedServiceId), aiService);
        if (!string.IsNullOrEmpty(defaultExecutionSettings!.ServiceId))
        {
            Assert.Equal(expectedServiceId, defaultExecutionSettings!.ServiceId);
        }
    }

    [Fact]
    public void ItGetsAIServiceConfigurationForTextGenerationByModelId()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton<ITextGenerationService>(null, new TextGenerationService("model1"));
        builder.Services.AddKeyedSingleton<ITextGenerationService>(null, new TextGenerationService("model2"));
        Kernel kernel = builder.Build();

        var arguments = new KernelArguments();
        var executionSettings = new PromptExecutionSettings() { ModelId = "model2" };
        var function = kernel.CreateFunctionFromPrompt("Hello AI", executionSettings: executionSettings);
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultExecutionSettings) = serviceSelector.SelectAIService<ITextGenerationService>(kernel, function, arguments);

        // Assert
        Assert.NotNull(aiService);
        Assert.Equal("model2", aiService.GetModelId());
        Assert.Equal(executionSettings, defaultExecutionSettings);
    }

    #region private
    private sealed class AIService : IAIService
    {
        public IReadOnlyDictionary<string, object?> Attributes => new Dictionary<string, object?>();
    }

    private sealed class TextGenerationService : ITextGenerationService
    {
        public IReadOnlyDictionary<string, object?> Attributes => this._attributes;

        private readonly Dictionary<string, object?> _attributes = new();

        public TextGenerationService(string modelId)
        {
            this._attributes.Add("ModelId", modelId);
        }

        public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }

        public IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }
    }
    #endregion
}

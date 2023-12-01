// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Services;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;
public class OrderedAIServiceConfigurationProviderTests
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
        Assert.Throws<KernelException>(() => serviceSelector.SelectAIService<ITextCompletion>(kernel, function, new KernelArguments()));
    }

    [Fact]
    public void ItGetsAIServiceConfigurationForSingleAIService()
    {
        // Arrange
        var kernel = new KernelBuilder().ConfigureServices(c =>
        {
            c.AddKeyedSingleton<IAIService>("service1", new AIService());
        }).Build();
        var function = kernel.CreateFunctionFromPrompt("Hello AI");
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultRequestSettings) = serviceSelector.SelectAIService<IAIService>(kernel, function, new KernelArguments());

        // Assert
        Assert.NotNull(aiService);
        Assert.Null(defaultRequestSettings);
    }

    [Fact]
    public void ItGetsAIServiceConfigurationForSingleTextCompletion()
    {
        // Arrange
        var kernel = new KernelBuilder().ConfigureServices(c =>
        {
            c.AddKeyedSingleton<ITextCompletion>("service1", new TextCompletion());
        }).Build();
        var function = kernel.CreateFunctionFromPrompt("Hello AI");
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultRequestSettings) = serviceSelector.SelectAIService<ITextCompletion>(kernel, function, new KernelArguments());

        // Assert
        Assert.NotNull(aiService);
        Assert.Null(defaultRequestSettings);
    }

    [Fact]
    public void ItGetsAIServiceConfigurationForTextCompletionByServiceId()
    {
        // Arrange
        var kernel = new KernelBuilder().ConfigureServices(c =>
        {
            c.AddKeyedSingleton<ITextCompletion>("service1", new TextCompletion());
            c.AddKeyedSingleton<ITextCompletion>("service2", new TextCompletion());
        }).Build();

        var executionSettings = new PromptExecutionSettings() { ServiceId = "service2" };
        var function = kernel.CreateFunctionFromPrompt("Hello AI", executionSettings);
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultExecutionSettings) = serviceSelector.SelectAIService<ITextCompletion>(kernel, function, new KernelArguments());

        // Assert
        Assert.Equal(kernel.GetService<ITextCompletion>("service2"), aiService);
        Assert.Equal(executionSettings, defaultExecutionSettings);
    }

    [Fact]
    public void ItThrowsAnSKExceptionForNotFoundService()
    {
        // Arrange
        var kernel = new KernelBuilder().ConfigureServices(c =>
        {
            c.AddKeyedSingleton<ITextCompletion>("service1", new TextCompletion());
            c.AddKeyedSingleton<ITextCompletion>("service2", new TextCompletion());
        }).Build();

        var executionSettings = new PromptExecutionSettings() { ServiceId = "service3" };
        var function = kernel.CreateFunctionFromPrompt("Hello AI", executionSettings);
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        // Assert
        Assert.Throws<KernelException>(() => serviceSelector.SelectAIService<ITextCompletion>(kernel, function, new KernelArguments()));
    }

    [Fact]
    public void ItUsesDefaultServiceForEmptyModelSettings()
    {
        // Arrange
        var kernel = new KernelBuilder().ConfigureServices(c =>
        {
            c.AddKeyedSingleton<ITextCompletion>("service1", new TextCompletion());
            c.AddKeyedSingleton<ITextCompletion>("service2", new TextCompletion());
        }).Build();
        var function = kernel.CreateFunctionFromPrompt("Hello AI");
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultRequestSettings) = serviceSelector.SelectAIService<ITextCompletion>(kernel, function, new KernelArguments());

        // Assert
        Assert.Equal(kernel.GetService<ITextCompletion>("service2"), aiService);
        Assert.Null(defaultRequestSettings);
    }

    [Fact]
    public void ItUsesDefaultServiceAndSettings()
    {
        // Arrange
        // Arrange
        var kernel = new KernelBuilder().ConfigureServices(c =>
        {
            c.AddKeyedSingleton<ITextCompletion>("service1", new TextCompletion());
            c.AddKeyedSingleton<ITextCompletion>("service2", new TextCompletion());
        }).Build();
        var executionSettings = new PromptExecutionSettings();
        var function = kernel.CreateFunctionFromPrompt("Hello AI", executionSettings);
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultRequestSettings) = serviceSelector.SelectAIService<ITextCompletion>(kernel, function, new KernelArguments());

        // Assert
        Assert.Equal(kernel.GetService<ITextCompletion>("service2"), aiService);
        Assert.Equal(executionSettings, defaultRequestSettings);
    }

    [Fact]
    public void ItUsesDefaultServiceAndSettingsEmptyServiceId()
    {
        // Arrange
        var kernel = new KernelBuilder().ConfigureServices(c =>
        {
            c.AddKeyedSingleton<ITextCompletion>("service1", new TextCompletion());
            c.AddKeyedSingleton<ITextCompletion>("service2", new TextCompletion());
        }).Build();
        var executionSettings = new PromptExecutionSettings() { ServiceId = "" };
        var function = kernel.CreateFunctionFromPrompt("Hello AI", executionSettings);
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultRequestSettings) = serviceSelector.SelectAIService<ITextCompletion>(kernel, function, new KernelArguments());

        // Assert
        Assert.Equal(kernel.GetService<ITextCompletion>("service2"), aiService);
        Assert.Equal(executionSettings, defaultRequestSettings);
    }

    [Theory]
    [InlineData(new string[] { "service1" }, "service1")]
    [InlineData(new string[] { "service2" }, "service2")]
    [InlineData(new string[] { "service3" }, "service3")]
    [InlineData(new string[] { "service4", "service1" }, "service1")]
    public void ItGetsAIServiceConfigurationByOrder(string[] serviceIds, string expectedServiceId)
    {
        // Arrange
        var kernel = new KernelBuilder().ConfigureServices(c =>
        {
            c.AddKeyedSingleton<ITextCompletion>("service1", new TextCompletion());
            c.AddKeyedSingleton<ITextCompletion>("service2", new TextCompletion());
            c.AddKeyedSingleton<ITextCompletion>("service3", new TextCompletion());
        }).Build();
        var executionSettings = new List<PromptExecutionSettings>();
        foreach (var serviceId in serviceIds)
        {
            executionSettings.Add(new PromptExecutionSettings() { ServiceId = serviceId });
        }
        var function = kernel.CreateFunctionFromPrompt(promptConfig: new PromptTemplateConfig() { Template = "Hello AI", ExecutionSettings = executionSettings });
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultRequestSettings) = serviceSelector.SelectAIService<ITextCompletion>(kernel, function, new KernelArguments());

        // Assert
        Assert.Equal(kernel.GetService<ITextCompletion>(expectedServiceId), aiService);
        Assert.Equal(expectedServiceId, defaultRequestSettings!.ServiceId);
    }

    [Fact]
    public void ItGetsAIServiceConfigurationForTextCompletionByModelId()
    {
        // Arrange
        var kernel = new KernelBuilder().ConfigureServices(c =>
        {
            c.AddKeyedSingleton<ITextCompletion>(null, new TextCompletion("model1"));
            c.AddKeyedSingleton<ITextCompletion>(null, new TextCompletion("model2"));
        }).Build();
        var arguments = new KernelArguments();
        var executionSettings = new PromptExecutionSettings() { ModelId = "model2" };
        var function = kernel.CreateFunctionFromPrompt("Hello AI", executionSettings: executionSettings);
        var serviceSelector = new OrderedAIServiceSelector();

        // Act
        (var aiService, var defaultExecutionSettings) = serviceSelector.SelectAIService<ITextCompletion>(kernel, function, arguments);

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

    private sealed class TextCompletion : ITextCompletion
    {
        public IReadOnlyDictionary<string, object?> Attributes => this._attributes;

        private readonly Dictionary<string, object?> _attributes = new();

        public TextCompletion(string? modelId = null)
        {
            if (modelId is not null)
            {
                this._attributes.Add("ModelId", modelId);
            }
        }

        public Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(string text, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }

        public IAsyncEnumerable<T> GetStreamingContentAsync<T>(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }
    }
    #endregion
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Functions;
using Microsoft.SemanticKernel.Services;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;
public class OrderedIAIServiceConfigurationProviderTests
{
    [Fact]
    public void ItThrowsAnSKExceptionForNoServices()
    {
        // Arrange
        var renderedPrompt = "Hello AI, what can you do for me?";
        var serviceCollection = new AIServiceCollection();
        var serviceProvider = serviceCollection.Build();
        var modelSettings = new List<AIRequestSettings>();
        var configurationProvider = new OrderedIAIServiceSelector();

        // Act
        // Assert
        Assert.Throws<SKException>(() => configurationProvider.SelectAIService<ITextCompletion>(renderedPrompt, serviceProvider, modelSettings));
    }

    [Fact]
    public void ItGetsAIServiceConfigurationForSingleAIService()
    {
        // Arrange
        var renderedPrompt = "Hello AI, what can you do for me?";
        var serviceCollection = new AIServiceCollection();
        serviceCollection.SetService<IAIService>(new AIService());
        var serviceProvider = serviceCollection.Build();
        var modelSettings = new List<AIRequestSettings>();
        var configurationProvider = new OrderedIAIServiceSelector();

        // Act
        (var aiService, var defaultRequestSettings) = configurationProvider.SelectAIService<IAIService>(renderedPrompt, serviceProvider, modelSettings);

        // Assert
        Assert.NotNull(aiService);
        Assert.Null(defaultRequestSettings);
    }

    [Fact]
    public void ItGetsAIServiceConfigurationForSingleTextCompletion()
    {
        // Arrange
        var renderedPrompt = "Hello AI, what can you do for me?";
        var serviceCollection = new AIServiceCollection();
        serviceCollection.SetService<ITextCompletion>(new TextCompletion());
        var serviceProvider = serviceCollection.Build();
        var modelSettings = new List<AIRequestSettings>();
        var configurationProvider = new OrderedIAIServiceSelector();

        // Act
        (var aiService, var defaultRequestSettings) = configurationProvider.SelectAIService<ITextCompletion>(renderedPrompt, serviceProvider, modelSettings);

        // Assert
        Assert.NotNull(aiService);
        Assert.Null(defaultRequestSettings);
    }

    [Fact]
    public void ItAIServiceConfigurationForTextCompletionByServiceId()
    {
        // Arrange
        var renderedPrompt = "Hello AI, what can you do for me?";
        var serviceCollection = new AIServiceCollection();
        serviceCollection.SetService<ITextCompletion>("service1", new TextCompletion());
        serviceCollection.SetService<ITextCompletion>("service2", new TextCompletion());
        var serviceProvider = serviceCollection.Build();
        var modelSettings = new List<AIRequestSettings>();
        var configurationProvider = new OrderedIAIServiceSelector();

        // Act
        (var aiService, var defaultRequestSettings) = configurationProvider.SelectAIService<ITextCompletion>(renderedPrompt, serviceProvider, modelSettings);

        // Assert
        Assert.NotNull(aiService);
        Assert.Null(defaultRequestSettings);
    }

    [Fact]
    public void ItThrowsAnSKExceptionForNotFoundService()
    {
        // Arrange
        var renderedPrompt = "Hello AI, what can you do for me?";
        var serviceCollection = new AIServiceCollection();
        serviceCollection.SetService<ITextCompletion>("service1", new TextCompletion());
        serviceCollection.SetService<ITextCompletion>("service2", new TextCompletion());
        var serviceProvider = serviceCollection.Build();
        var modelSettings = new List<AIRequestSettings>
        {
            new AIRequestSettings() { ServiceId = "service3" }
        };
        var configurationProvider = new OrderedIAIServiceSelector();

        // Act
        // Assert
        Assert.Throws<SKException>(() => configurationProvider.SelectAIService<ITextCompletion>(renderedPrompt, serviceProvider, modelSettings));
    }

    [Fact]
    public void ItUsesDefaultServiceForNullModelSettings()
    {
        // Arrange
        var renderedPrompt = "Hello AI, what can you do for me?";
        var serviceCollection = new AIServiceCollection();
        serviceCollection.SetService<ITextCompletion>("service1", new TextCompletion());
        serviceCollection.SetService<ITextCompletion>("service2", new TextCompletion(), true);
        var serviceProvider = serviceCollection.Build();
        var configurationProvider = new OrderedIAIServiceSelector();

        // Act
        (var aiService, var defaultRequestSettings) = configurationProvider.SelectAIService<ITextCompletion>(renderedPrompt, serviceProvider, null);

        // Assert
        Assert.Equal(serviceProvider.GetService<ITextCompletion>("service2"), aiService);
        Assert.Null(defaultRequestSettings);
    }

    [Fact]
    public void ItUsesDefaultServiceForEmptyModelSettings()
    {
        // Arrange
        var renderedPrompt = "Hello AI, what can you do for me?";
        var serviceCollection = new AIServiceCollection();
        serviceCollection.SetService<ITextCompletion>("service1", new TextCompletion());
        serviceCollection.SetService<ITextCompletion>("service2", new TextCompletion(), true);
        var serviceProvider = serviceCollection.Build();
        var modelSettings = new List<AIRequestSettings>();
        var configurationProvider = new OrderedIAIServiceSelector();

        // Act
        (var aiService, var defaultRequestSettings) = configurationProvider.SelectAIService<ITextCompletion>(renderedPrompt, serviceProvider, modelSettings);

        // Assert
        Assert.Equal(serviceProvider.GetService<ITextCompletion>("service2"), aiService);
        Assert.Null(defaultRequestSettings);
    }

    [Fact]
    public void ItUsesDefaultServiceAndSettings()
    {
        // Arrange
        var renderedPrompt = "Hello AI, what can you do for me?";
        var serviceCollection = new AIServiceCollection();
        serviceCollection.SetService<ITextCompletion>("service1", new TextCompletion());
        serviceCollection.SetService<ITextCompletion>("service2", new TextCompletion(), true);
        var serviceProvider = serviceCollection.Build();
        var modelSettings = new List<AIRequestSettings>
        {
            new AIRequestSettings()
        };
        var configurationProvider = new OrderedIAIServiceSelector();

        // Act
        (var aiService, var defaultRequestSettings) = configurationProvider.SelectAIService<ITextCompletion>(renderedPrompt, serviceProvider, modelSettings);

        // Assert
        Assert.Equal(serviceProvider.GetService<ITextCompletion>("service2"), aiService);
        Assert.Equal(modelSettings[0], defaultRequestSettings);
    }

    [Fact]
    public void ItUsesDefaultServiceAndSettingsEmptyServiceId()
    {
        // Arrange
        var renderedPrompt = "Hello AI, what can you do for me?";
        var serviceCollection = new AIServiceCollection();
        serviceCollection.SetService<ITextCompletion>("service1", new TextCompletion());
        serviceCollection.SetService<ITextCompletion>("service2", new TextCompletion(), true);
        var serviceProvider = serviceCollection.Build();
        var modelSettings = new List<AIRequestSettings>
        {
            new AIRequestSettings() { ServiceId = "" }
        };
        var configurationProvider = new OrderedIAIServiceSelector();

        // Act
        (var aiService, var defaultRequestSettings) = configurationProvider.SelectAIService<ITextCompletion>(renderedPrompt, serviceProvider, modelSettings);

        // Assert
        Assert.Equal(serviceProvider.GetService<ITextCompletion>("service2"), aiService);
        Assert.Equal(modelSettings[0], defaultRequestSettings);
    }

    [Theory]
    [InlineData(new string[] { "service1" }, "service1")]
    [InlineData(new string[] { "service2" }, "service2")]
    [InlineData(new string[] { "service3" }, "service3")]
    [InlineData(new string[] { "service4", "service1" }, "service1")]
    public void ItGetsAIServiceConfigurationByOrder(string[] serviceIds, string expectedServiceId)
    {
        // Arrange
        var renderedPrompt = "Hello AI, what can you do for me?";
        var serviceCollection = new AIServiceCollection();
        serviceCollection.SetService<ITextCompletion>("service1", new TextCompletion());
        serviceCollection.SetService<ITextCompletion>("service2", new TextCompletion());
        serviceCollection.SetService<ITextCompletion>("service3", new TextCompletion());
        var serviceProvider = serviceCollection.Build();
        var modelSettings = new List<AIRequestSettings>();
        foreach (var serviceId in serviceIds)
        {
            modelSettings.Add(new AIRequestSettings() { ServiceId = serviceId });
        }
        var configurationProvider = new OrderedIAIServiceSelector();

        // Act
        (var aiService, var defaultRequestSettings) = configurationProvider.SelectAIService<ITextCompletion>(renderedPrompt, serviceProvider, modelSettings);

        // Assert
        Assert.Equal(serviceProvider.GetService<ITextCompletion>(expectedServiceId), aiService);
        Assert.Equal(expectedServiceId, defaultRequestSettings!.ServiceId);
    }

    #region private
    private sealed class AIService : IAIService
    {
    }

    private sealed class TextCompletion : ITextCompletion
    {
        public Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(string text, AIRequestSettings? requestSettings = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }

        public IAsyncEnumerable<ITextStreamingResult> GetStreamingCompletionsAsync(string text, AIRequestSettings? requestSettings = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }
    }
    #endregion
}

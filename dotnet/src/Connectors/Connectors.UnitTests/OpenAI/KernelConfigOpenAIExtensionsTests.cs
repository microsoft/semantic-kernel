// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Services;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI;

/// <summary>
/// Unit tests of <see cref="KernelConfigOpenAIExtensions"/>.
/// </summary>
public class KernelConfigOpenAIExtensionsTests
{
    [Fact]
    public void ItSucceedsWhenAddingDifferentServiceTypeWithSameId()
    {
        var target = new ServiceRegistry();
        target.AddAzureTextCompletionService("azure", "depl", "https://url", "key");
        target.AddAzureTextEmbeddingGenerationService("azure", "depl2", "https://url", "key");

        Assert.Contains("azure", target.GetTextCompletionServiceIds());
        Assert.Contains("azure", target.GetTextEmbeddingGenerationServiceIds());
    }

    [Fact]
    public void ItTellsIfAServiceIsAvailable()
    {
        // Arrange
        var target = new ServiceRegistry();
        target.AddAzureTextCompletionService("azure", "depl", "https://url", "key");
        target.AddOpenAITextCompletionService("oai", "model", "apikey");
        target.AddAzureTextEmbeddingGenerationService("azure", "depl2", "https://url2", "key");
        target.AddOpenAITextEmbeddingGenerationService("oai2", "model2", "apikey2");

        // Assert
        var completionServices = target.GetTextCompletionServiceIds();
        Assert.Contains("azure", completionServices);
        Assert.Contains("oai", completionServices);
        Assert.DoesNotContain("azure2", completionServices);
        Assert.DoesNotContain("oai2", completionServices);

        var embeddingServices = target.GetTextEmbeddingGenerationServiceIds();
        Assert.Contains("azure", embeddingServices);
        Assert.Contains("oai2", embeddingServices);
        Assert.DoesNotContain("azure1", embeddingServices);
        Assert.DoesNotContain("oai", embeddingServices);
    }

    [Fact]
    public void ItCanOverwriteServices()
    {
        // Arrange
        var target = new ServiceRegistry();

        // Act - Assert no exception occurs
        target.AddAzureTextCompletionService("one", "dep", "https://localhost", "key");
        target.AddAzureTextCompletionService("one", "dep", "https://localhost", "key");
        target.AddOpenAITextCompletionService("one", "model", "key");
        target.AddOpenAITextCompletionService("one", "model", "key");
        target.AddAzureTextEmbeddingGenerationService("one", "dep", "https://localhost", "key");
        target.AddAzureTextEmbeddingGenerationService("one", "dep", "https://localhost", "key");
        target.AddOpenAITextEmbeddingGenerationService("one", "model", "key");
        target.AddOpenAITextEmbeddingGenerationService("one", "model", "key");
    }

    [Fact]
    public void ItCanRemoveAllServices()
    {
        // Arrange
        var target = new ServiceRegistry();
        target.AddAzureTextCompletionService("one", "dep", "https://localhost", "key");
        target.AddAzureTextCompletionService("2", "dep", "https://localhost", "key");
        target.AddOpenAITextCompletionService("3", "model", "key");
        target.AddOpenAITextCompletionService("4", "model", "key");
        target.AddAzureTextEmbeddingGenerationService("5", "dep", "https://localhost", "key");
        target.AddAzureTextEmbeddingGenerationService("6", "dep", "https://localhost", "key");
        target.AddOpenAITextEmbeddingGenerationService("7", "model", "key");
        target.AddOpenAITextEmbeddingGenerationService("8", "model", "key");

        // Act
        target.RemoveAllTextCompletionServices();
        target.RemoveAllTextEmbeddingGenerationServices();

        // Assert
        Assert.Empty(target.GetTextEmbeddingGenerationServiceIds());
        Assert.Empty(target.GetTextCompletionServiceIds());
    }

    [Fact]
    public void ItCanRemoveAllTextCompletionServices()
    {
        // Arrange
        var target = new ServiceRegistry();
        target.AddAzureTextCompletionService("one", "dep", "https://localhost", "key");
        target.AddAzureTextCompletionService("2", "dep", "https://localhost", "key");
        target.AddOpenAITextCompletionService("3", "model", "key");
        target.AddOpenAITextCompletionService("4", "model", "key");
        target.AddAzureTextEmbeddingGenerationService("5", "dep", "https://localhost", "key");
        target.AddAzureTextEmbeddingGenerationService("6", "dep", "https://localhost", "key");
        target.AddOpenAITextEmbeddingGenerationService("7", "model", "key");
        target.AddOpenAITextEmbeddingGenerationService("8", "model", "key");

        // Act
        target.RemoveAllTextCompletionServices();

        // Assert
        Assert.Equal(4, target.GetTextEmbeddingGenerationServiceIds().Count());
        Assert.Empty(target.GetTextCompletionServiceIds());
    }

    [Fact]
    public void ItCanRemoveAllTextEmbeddingGenerationServices()
    {
        // Arrange
        var target = new ServiceRegistry();
        target.AddAzureTextCompletionService("one", "dep", "https://localhost", "key");
        target.AddAzureTextCompletionService("2", "dep", "https://localhost", "key");
        target.AddOpenAITextCompletionService("3", "model", "key");
        target.AddOpenAITextCompletionService("4", "model", "key");
        target.AddAzureTextEmbeddingGenerationService("5", "dep", "https://localhost", "key");
        target.AddAzureTextEmbeddingGenerationService("6", "dep", "https://localhost", "key");
        target.AddOpenAITextEmbeddingGenerationService("7", "model", "key");
        target.AddOpenAITextEmbeddingGenerationService("8", "model", "key");

        // Act
        target.RemoveAllTextEmbeddingGenerationServices();

        // Assert
        Assert.Equal(4, target.GetTextCompletionServiceIds().Count());
        Assert.Empty(target.GetTextEmbeddingGenerationServiceIds());
    }

    //[Fact]
    //public void ItCanRemoveOneCompletionService()
    //{
    //    // Arrange
    //    var target = new NamedServiceCollection();
    //    target.AddAzureTextCompletionService("1", "dep", "https://localhost", "key");
    //    target.AddAzureTextCompletionService("2", "dep", "https://localhost", "key");
    //    target.AddOpenAITextCompletionService("3", "model", "key");
    //    Assert.Equal("1", target.DefaultTextCompletionServiceId);

    //    // Act - Assert
    //    Assert.True(target.TryRemoveTextCompletionService("1"));
    //    Assert.Equal("2", target.DefaultTextCompletionServiceId);
    //    Assert.True(target.TryRemoveTextCompletionService("2"));
    //    Assert.Equal("3", target.DefaultTextCompletionServiceId);
    //    Assert.True(target.TryRemoveTextCompletionService("3"));
    //    Assert.Null(target.DefaultTextCompletionServiceId);
    //}

    //[Fact]
    //public void ItCanRemoveOneTextEmbeddingGenerationService()
    //{
    //    // Arrange
    //    var target = new NamedServiceCollection();
    //    target.AddAzureTextEmbeddingGenerationService("1", "dep", "https://localhost", "key");
    //    target.AddAzureTextEmbeddingGenerationService("2", "dep", "https://localhost", "key");
    //    target.AddOpenAITextEmbeddingGenerationService("3", "model", "key");
    //    Assert.Equal("1", target.DefaultTextEmbeddingGenerationServiceId);

    //    // Act - Assert
    //    Assert.True(target.TryRemoveTextEmbeddingGenerationService("1"));
    //    Assert.Equal("2", target.DefaultTextEmbeddingGenerationServiceId);
    //    Assert.True(target.TryRemoveTextEmbeddingGenerationService("2"));
    //    Assert.Equal("3", target.DefaultTextEmbeddingGenerationServiceId);
    //    Assert.True(target.TryRemoveTextEmbeddingGenerationService("3"));
    //    Assert.Null(target.DefaultTextEmbeddingGenerationServiceId);
    //}

    //[Fact]
    //public void GetTextEmbeddingGenerationServiceItReturnsDefaultWhenNonExistingIdIsProvided()
    //{
    //    // Arrange
    //    var target = new NamedServiceCollection();
    //    target.AddOpenAITextEmbeddingGenerationService("1", "dep", "https://localhost", "key");
    //    target.AddAzureTextEmbeddingGenerationService("2", "dep", "https://localhost", "key");
    //    target.SetDefaultTextEmbeddingGenerationService("2");

    //    // Act
    //    var result = target.GetTextEmbeddingGenerationServiceOrDefault("test");

    //    // Assert
    //    Assert.Equal("2", result);
    //}

    //[Fact]
    //public void GetEmbeddingServiceReturnsSpecificWhenExistingIdIsProvided()
    //{
    //    // Arrange
    //    var kernel = new Mock<IKernel>();
    //    var target = new NamedServiceCollection();
    //    target.AddOpenAITextEmbeddingGenerationService("1", "dep", "https://localhost", "key");
    //    target.AddAzureTextEmbeddingGenerationService("2", "dep", "https://localhost", "key");
    //    target.SetDefaultTextEmbeddingGenerationService("2");

    //    // Act
    //    var result = target.GetTextEmbeddingGenerationServiceOrDefault("1");

    //    // Assert
    //    Assert.Equal("1", result);
    //}

    //[Fact]
    //public void GetEmbeddingServiceReturnsDefaultWhenNoIdIsProvided()
    //{
    //    // Arrange
    //    var kernel = new Mock<IKernel>();
    //    var target = new NamedServiceCollection();
    //    target.AddOpenAITextEmbeddingGenerationService("1", "dep", "https://localhost", "key");
    //    target.AddAzureTextEmbeddingGenerationService("2", "dep", "https://localhost", "key");
    //    target.SetDefaultTextEmbeddingGenerationService("2");

    //    // Act
    //    var result = target.GetTextEmbeddingGenerationServiceOrDefault();

    //    // Assert
    //    Assert.Equal("2", result);
    //}

    //[Fact]
    //public void GetTextCompletionServiceReturnsDefaultWhenNonExistingIdIsProvided()
    //{
    //    // Arrange
    //    var kernel = new Mock<IKernel>();
    //    var target = new NamedServiceCollection();
    //    target.AddOpenAITextCompletionService("1", "dep", "https://localhost", "key");
    //    target.AddAzureTextCompletionService("2", "dep", "https://localhost", "key");
    //    target.SetDefaultTextCompletionService("2");

    //    // Act
    //    var result = target.GetTextCompletionServiceOrDefault("345");

    //    // Assert
    //    Assert.Equal("2", result);
    //}

    //[Fact]
    //public void GetTextCompletionServiceReturnsSpecificWhenExistingIdIsProvided()
    //{
    //    // Arrange
    //    var kernel = new Mock<IKernel>();
    //    var target = new NamedServiceCollection();
    //    target.AddOpenAITextCompletionService("1", "dep", "https://localhost", "key");
    //    target.AddAzureTextCompletionService("2", "dep", "https://localhost", "key");
    //    target.SetDefaultTextCompletionService("2");

    //    // Act
    //    var result = target.GetTextCompletionServiceOrDefault("1");

    //    // Assert
    //    Assert.Equal("1", result);
    //}

    //[Fact]
    //public void GetTextCompletionServiceItReturnsDefaultWhenNoIdIsProvided()
    //{
    //    // Arrange
    //    var kernel = new Mock<IKernel>();
    //    var target = new NamedServiceCollection();
    //    target.AddOpenAITextCompletionService("1", "dep", "https://localhost", "key");
    //    target.AddAzureTextCompletionService("2", "dep", "https://localhost", "key");
    //    target.SetDefaultTextCompletionService("2");

    //    // Act
    //    var result = target.GetTextCompletionServiceOrDefault();

    //    // Assert
    //    Assert.Equal("2", result);
    //}
}

// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI;

/// <summary>
/// Unit tests of <see cref="OpenAIKernelConfigExtensions"/>.
/// </summary>
[System.Obsolete("All the methods of this class are deprecated and it will be removed in one of the next SK SDK versions.")]
public class KernelConfigOpenAIExtensionsTests
{
    [Fact]
    public void ItSucceedsWhenAddingDifferentServiceTypeWithSameId()
    {
        var target = new KernelConfig();
        target.AddAzureTextCompletionService("depl", "https://url", "key", serviceId: "azure");
        target.AddAzureTextEmbeddingGenerationService("depl2", "https://url", "key", serviceId: "azure");

        Assert.True(target.TextCompletionServices.ContainsKey("azure"));
        Assert.True(target.TextEmbeddingGenerationServices.ContainsKey("azure"));
    }

    [Fact]
    public void ItTellsIfAServiceIsAvailable()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureTextCompletionService("deployment1", "https://url", "key", serviceId: "azure");
        target.AddOpenAITextCompletionService("model", "apikey", serviceId: "oai");
        target.AddAzureTextEmbeddingGenerationService("deployment2", "https://url2", "key", serviceId: "azure");
        target.AddOpenAITextEmbeddingGenerationService("model2", "apikey2", serviceId: "oai2");

        // Assert
        Assert.True(target.TextCompletionServices.ContainsKey("azure"));
        Assert.True(target.TextCompletionServices.ContainsKey("oai"));
        Assert.True(target.TextEmbeddingGenerationServices.ContainsKey("azure"));
        Assert.True(target.TextEmbeddingGenerationServices.ContainsKey("oai2"));

        Assert.False(target.TextCompletionServices.ContainsKey("azure2"));
        Assert.False(target.TextCompletionServices.ContainsKey("oai2"));
        Assert.False(target.TextEmbeddingGenerationServices.ContainsKey("azure1"));
        Assert.False(target.TextEmbeddingGenerationServices.ContainsKey("oai"));
    }

    [Fact]
    public void ItCanOverwriteServices()
    {
        // Arrange
        var target = new KernelConfig();

        // Act - Assert no exception occurs
        target.AddAzureTextCompletionService("dep", "https://localhost", "key", serviceId: "one");
        target.AddAzureTextCompletionService("dep", "https://localhost", "key", serviceId: "one");
        target.AddOpenAITextCompletionService("model", "key", serviceId: "one");
        target.AddOpenAITextCompletionService("model", "key", serviceId: "one");
        target.AddAzureTextEmbeddingGenerationService("dep", "https://localhost", "key", serviceId: "one");
        target.AddAzureTextEmbeddingGenerationService("dep", "https://localhost", "key", serviceId: "one");
        target.AddOpenAITextEmbeddingGenerationService("model", "key", serviceId: "one");
        target.AddOpenAITextEmbeddingGenerationService("model", "key", serviceId: "one");
    }

    [Fact]
    public void ItCanRemoveAllServices()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureTextCompletionService("dep", "https://localhost", "key", serviceId: "one");
        target.AddAzureTextCompletionService("dep", "https://localhost", "key", serviceId: "2");
        target.AddOpenAITextCompletionService("model", "key", serviceId: "3");
        target.AddOpenAITextCompletionService("model", "key", serviceId: "4");
        target.AddAzureTextEmbeddingGenerationService("dep", "https://localhost", "key", serviceId: "5");
        target.AddAzureTextEmbeddingGenerationService("dep", "https://localhost", "key", serviceId: "6");
        target.AddOpenAITextEmbeddingGenerationService("model", "key", serviceId: "7");
        target.AddOpenAITextEmbeddingGenerationService("model", "key", serviceId: "8");

        // Act
        target.RemoveAllTextCompletionServices();
        target.RemoveAllTextEmbeddingGenerationServices();

        // Assert
        Assert.Empty(target.TextEmbeddingGenerationServices);
        Assert.Empty(target.TextCompletionServices);
    }

    [Fact]
    public void ItCanRemoveAllTextCompletionServices()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureTextCompletionService("dep", "https://localhost", "key", serviceId: "one");
        target.AddAzureTextCompletionService("dep", "https://localhost", "key", serviceId: "2");
        target.AddOpenAITextCompletionService("model", "key", serviceId: "3");
        target.AddOpenAITextCompletionService("model", "key", serviceId: "4");

        target.AddAzureTextEmbeddingGenerationService("dep", "https://localhost", "key", serviceId: "5");
        target.AddAzureTextEmbeddingGenerationService("dep", "https://localhost", "key", serviceId: "6");
        target.AddOpenAITextEmbeddingGenerationService("model", "key", serviceId: "7");
        target.AddOpenAITextEmbeddingGenerationService("model", "key", serviceId: "8");

        // Act
        target.RemoveAllTextCompletionServices();

        // Assert (+1 for the default)
        Assert.Equal(4 + 1, target.TextEmbeddingGenerationServices.Count);
    }

    [Fact]
    public void ItCanRemoveAllTextEmbeddingGenerationServices()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureTextCompletionService("dep", "https://localhost", "key", serviceId: "one");
        target.AddAzureTextCompletionService("dep", "https://localhost", "key", serviceId: "2");
        target.AddOpenAITextCompletionService("model", "key", serviceId: "3");
        target.AddOpenAITextCompletionService("model", "key", serviceId: "4");
        target.AddAzureTextEmbeddingGenerationService("dep", "https://localhost", "key", serviceId: "5");
        target.AddAzureTextEmbeddingGenerationService("dep", "https://localhost", "key", serviceId: "6");
        target.AddOpenAITextEmbeddingGenerationService("model", "key", serviceId: "7");
        target.AddOpenAITextEmbeddingGenerationService("model", "key", serviceId: "8");

        // Act
        target.RemoveAllTextEmbeddingGenerationServices();

        // Assert (+1 for the default)
        Assert.Equal(4 + 1, target.TextCompletionServices.Count);
        Assert.Empty(target.TextEmbeddingGenerationServices);
    }
}

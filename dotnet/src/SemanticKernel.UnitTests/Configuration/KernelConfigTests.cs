// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.OpenAI.Services;
using Microsoft.SemanticKernel.Configuration;
using Microsoft.SemanticKernel.Reliability;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Configuration;

/// <summary>
/// Unit tests of <see cref="KernelConfig"/>.
/// </summary>
public class KernelConfigTests
{
    [Fact]
    public void HttpRetryHandlerFactoryIsSet()
    {
        // Arrange
        var retry = new NullHttpRetryHandlerFactory();
        var config = new KernelConfig();

        // Act
        config.SetHttpRetryHandlerFactory(retry);

        // Assert
        Assert.Equal(retry, config.HttpHandlerFactory);
    }

    [Fact]
    public void HttpRetryHandlerFactoryIsSetWithCustomImplementation()
    {
        // Arrange
        var retry = new Mock<IDelegatingHandlerFactory>();
        var config = new KernelConfig();

        // Act
        config.SetHttpRetryHandlerFactory(retry.Object);

        // Assert
        Assert.Equal(retry.Object, config.HttpHandlerFactory);
    }

    [Fact]
    public void HttpRetryHandlerFactoryIsSetToDefaultHttpRetryHandlerFactoryIfNull()
    {
        // Arrange
        var config = new KernelConfig();

        // Act
        config.SetHttpRetryHandlerFactory(null);

        // Assert
        Assert.IsType<DefaultHttpRetryHandlerFactory>(config.HttpHandlerFactory);
    }

    [Fact]
    public void HttpRetryHandlerFactoryIsSetToDefaultHttpRetryHandlerFactoryIfNotSet()
    {
        // Arrange
        var config = new KernelConfig();

        // Act
        // Assert
        Assert.IsType<DefaultHttpRetryHandlerFactory>(config.HttpHandlerFactory);
    }

    [Fact]
    public void ItFailsWhenAddingCompletionBackendsWithSameLabel()
    {
        var target = new KernelConfig();
        target.AddAzureOpenAICompletionBackend("azure", "depl", "https://url", "key");

        var exception = Assert.Throws<KernelException>(() =>
        {
            target.AddAzureOpenAICompletionBackend("azure", "depl2", "https://url", "key");
        });
        Assert.Equal(KernelException.ErrorCodes.InvalidBackendConfiguration, exception.ErrorCode);
    }

    [Fact]
    public void ItFailsWhenAddingEmbeddingsBackendsWithSameLabel()
    {
        var target = new KernelConfig();
        target.AddAzureOpenAIEmbeddingsBackend("azure", "depl", "https://url", "key");

        var exception = Assert.Throws<KernelException>(() =>
        {
            target.AddAzureOpenAIEmbeddingsBackend("azure", "depl2", "https://url", "key");
        });
        Assert.Equal(KernelException.ErrorCodes.InvalidBackendConfiguration, exception.ErrorCode);
    }

    [Fact]
    public void ItSucceedsWhenAddingDifferentBackendTypeWithSameLabel()
    {
        var target = new KernelConfig();
        target.AddAzureOpenAICompletionBackend("azure", "depl", "https://url", "key");
        target.AddAzureOpenAIEmbeddingsBackend("azure", "depl2", "https://url", "key");

        Assert.True(target.HasCompletionBackend("azure"));
        Assert.True(target.HasEmbeddingsBackend("azure"));
    }

    [Fact]
    public void ItFailsWhenSetNonExistentCompletionBackend()
    {
        var target = new KernelConfig();
        var exception = Assert.Throws<KernelException>(() =>
        {
            target.SetDefaultCompletionBackend("azure");
        });
        Assert.Equal(KernelException.ErrorCodes.BackendNotFound, exception.ErrorCode);
    }

    [Fact]
    public void ItFailsWhenSetNonExistentEmbeddingBackend()
    {
        var target = new KernelConfig();
        var exception = Assert.Throws<KernelException>(() =>
        {
            target.SetDefaultEmbeddingsBackend("azure");
        });
        Assert.Equal(KernelException.ErrorCodes.BackendNotFound, exception.ErrorCode);
    }

    [Fact]
    public void ItTellsIfABackendIsAvailable()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureOpenAICompletionBackend("azure", "depl", "https://url", "key");
        target.AddOpenAICompletionBackend("oai", "model", "apikey");
        target.AddAzureOpenAIEmbeddingsBackend("azure", "depl2", "https://url2", "key");
        target.AddOpenAIEmbeddingsBackend("oai2", "model2", "apikey2");

        // Assert
        Assert.True(target.HasCompletionBackend("azure"));
        Assert.True(target.HasCompletionBackend("oai"));
        Assert.True(target.HasEmbeddingsBackend("azure"));
        Assert.True(target.HasEmbeddingsBackend("oai2"));

        Assert.False(target.HasCompletionBackend("azure2"));
        Assert.False(target.HasCompletionBackend("oai2"));
        Assert.False(target.HasEmbeddingsBackend("azure1"));
        Assert.False(target.HasEmbeddingsBackend("oai"));

        Assert.True(target.HasCompletionBackend("azure",
            x => x is AzureOpenAIConfig));
        Assert.False(target.HasCompletionBackend("azure",
            x => x is OpenAIConfig));

        Assert.False(target.HasEmbeddingsBackend("oai2",
            x => x is AzureOpenAIConfig));
        Assert.True(target.HasEmbeddingsBackend("oai2",
            x => x is OpenAIConfig));

        Assert.True(target.HasCompletionBackend("azure",
            x => x is AzureOpenAIConfig azureConfig && azureConfig.DeploymentName == "depl"));
        Assert.False(target.HasCompletionBackend("azure",
            x => x is AzureOpenAIConfig azureConfig && azureConfig.DeploymentName == "nope"));
    }

    [Fact]
    public void ItCanOverwriteBackends()
    {
        // Arrange
        var target = new KernelConfig();

        // Act - Assert no exception occurs
        target.AddAzureOpenAICompletionBackend("one", "dep", "https://localhost", "key", overwrite: true);
        target.AddAzureOpenAICompletionBackend("one", "dep", "https://localhost", "key", overwrite: true);
        target.AddOpenAICompletionBackend("one", "model", "key", overwrite: true);
        target.AddOpenAICompletionBackend("one", "model", "key", overwrite: true);
        target.AddAzureOpenAIEmbeddingsBackend("one", "dep", "https://localhost", "key", overwrite: true);
        target.AddAzureOpenAIEmbeddingsBackend("one", "dep", "https://localhost", "key", overwrite: true);
        target.AddOpenAIEmbeddingsBackend("one", "model", "key", overwrite: true);
        target.AddOpenAIEmbeddingsBackend("one", "model", "key", overwrite: true);
    }

    [Fact]
    public void ItCanRemoveAllBackends()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureOpenAICompletionBackend("one", "dep", "https://localhost", "key");
        target.AddAzureOpenAICompletionBackend("2", "dep", "https://localhost", "key");
        target.AddOpenAICompletionBackend("3", "model", "key");
        target.AddOpenAICompletionBackend("4", "model", "key");
        target.AddAzureOpenAIEmbeddingsBackend("5", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingsBackend("6", "dep", "https://localhost", "key");
        target.AddOpenAIEmbeddingsBackend("7", "model", "key");
        target.AddOpenAIEmbeddingsBackend("8", "model", "key");

        // Act
        target.RemoveAllBackends();

        // Assert
        Assert.Empty(target.GetAllEmbeddingsBackends());
        Assert.Empty(target.GetAllCompletionBackends());
    }

    [Fact]
    public void ItCanRemoveAllCompletionBackends()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureOpenAICompletionBackend("one", "dep", "https://localhost", "key");
        target.AddAzureOpenAICompletionBackend("2", "dep", "https://localhost", "key");
        target.AddOpenAICompletionBackend("3", "model", "key");
        target.AddOpenAICompletionBackend("4", "model", "key");
        target.AddAzureOpenAIEmbeddingsBackend("5", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingsBackend("6", "dep", "https://localhost", "key");
        target.AddOpenAIEmbeddingsBackend("7", "model", "key");
        target.AddOpenAIEmbeddingsBackend("8", "model", "key");

        // Act
        target.RemoveAllCompletionBackends();

        // Assert
        Assert.Equal(4, target.GetAllEmbeddingsBackends().Count());
        Assert.Empty(target.GetAllCompletionBackends());
    }

    [Fact]
    public void ItCanRemoveAllEmbeddingsBackends()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureOpenAICompletionBackend("one", "dep", "https://localhost", "key");
        target.AddAzureOpenAICompletionBackend("2", "dep", "https://localhost", "key");
        target.AddOpenAICompletionBackend("3", "model", "key");
        target.AddOpenAICompletionBackend("4", "model", "key");
        target.AddAzureOpenAIEmbeddingsBackend("5", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingsBackend("6", "dep", "https://localhost", "key");
        target.AddOpenAIEmbeddingsBackend("7", "model", "key");
        target.AddOpenAIEmbeddingsBackend("8", "model", "key");

        // Act
        target.RemoveAllEmbeddingBackends();

        // Assert
        Assert.Equal(4, target.GetAllCompletionBackends().Count());
        Assert.Empty(target.GetAllEmbeddingsBackends());
    }

    [Fact]
    public void ItCanRemoveOneCompletionBackend()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureOpenAICompletionBackend("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAICompletionBackend("2", "dep", "https://localhost", "key");
        target.AddOpenAICompletionBackend("3", "model", "key");
        Assert.Equal("1", target.DefaultCompletionBackend);

        // Act - Assert
        target.RemoveCompletionBackend("1");
        Assert.Equal("2", target.DefaultCompletionBackend);
        target.RemoveCompletionBackend("2");
        Assert.Equal("3", target.DefaultCompletionBackend);
        target.RemoveCompletionBackend("3");
        Assert.Null(target.DefaultCompletionBackend);
    }

    [Fact]
    public void ItCanRemoveOneEmbeddingsBackend()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureOpenAIEmbeddingsBackend("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingsBackend("2", "dep", "https://localhost", "key");
        target.AddOpenAIEmbeddingsBackend("3", "model", "key");
        Assert.Equal("1", target.DefaultEmbeddingsBackend);

        // Act - Assert
        target.RemoveEmbeddingsBackend("1");
        Assert.Equal("2", target.DefaultEmbeddingsBackend);
        target.RemoveEmbeddingsBackend("2");
        Assert.Equal("3", target.DefaultEmbeddingsBackend);
        target.RemoveEmbeddingsBackend("3");
        Assert.Null(target.DefaultEmbeddingsBackend);
    }

    [Fact]
    public void GetEmbeddingsBackendItReturnsDefaultWhenNonExistingLabelIsProvided()
    {
        // Arrange
        var target = new KernelConfig();
        var defaultBackendLabel = "2";
        target.AddAzureOpenAIEmbeddingsBackend("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingsBackend(defaultBackendLabel, "dep", "https://localhost", "key");
        target.SetDefaultEmbeddingsBackend(defaultBackendLabel);

        // Act
        var result = target.GetEmbeddingsBackend("test");

        // Assert
        Assert.IsType<AzureOpenAIConfig>(result);
        Assert.Equal(defaultBackendLabel, result.Label);
    }

    [Fact]
    public void GetEmbeddingsBackendItReturnsSpecificWhenExistingLabelIsProvided()
    {
        // Arrange
        var target = new KernelConfig();
        var specificBackendLabel = "1";
        var defaultBackendLabel = "2";
        target.AddOpenAIEmbeddingsBackend(specificBackendLabel, "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingsBackend(defaultBackendLabel, "dep", "https://localhost", "key");
        target.SetDefaultEmbeddingsBackend(defaultBackendLabel);

        // Act
        var result = target.GetEmbeddingsBackend(specificBackendLabel);

        // Assert
        Assert.IsType<OpenAIConfig>(result);
        Assert.Equal(specificBackendLabel, result.Label);
    }

    [Fact]
    public void GetEmbeddingsBackendItReturnsDefaultWhenNoLabelIsProvided()
    {
        // Arrange
        var target = new KernelConfig();
        var defaultBackendLabel = "2";
        target.AddAzureOpenAIEmbeddingsBackend("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingsBackend(defaultBackendLabel, "dep", "https://localhost", "key");
        target.SetDefaultEmbeddingsBackend(defaultBackendLabel);

        // Act
        var result = target.GetEmbeddingsBackend();

        // Assert
        Assert.IsType<AzureOpenAIConfig>(result);
        Assert.Equal(defaultBackendLabel, result.Label);
    }

    [Fact]
    public void GetCompletionBackendItReturnsDefaultWhenNonExistingLabelIsProvided()
    {
        // Arrange
        var target = new KernelConfig();
        var defaultBackendLabel = "2";
        target.AddAzureOpenAICompletionBackend("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAICompletionBackend(defaultBackendLabel, "dep", "https://localhost", "key");
        target.SetDefaultCompletionBackend(defaultBackendLabel);

        // Act
        var result = target.GetCompletionBackend("test");

        // Assert
        Assert.IsType<AzureOpenAIConfig>(result);
        Assert.Equal(defaultBackendLabel, result.Label);
    }

    [Fact]
    public void GetCompletionBackendItReturnsSpecificWhenExistingLabelIsProvided()
    {
        // Arrange
        var target = new KernelConfig();
        var specificBackendLabel = "1";
        var defaultBackendLabel = "2";
        target.AddOpenAICompletionBackend(specificBackendLabel, "dep", "https://localhost", "key");
        target.AddAzureOpenAICompletionBackend(defaultBackendLabel, "dep", "https://localhost", "key");
        target.SetDefaultCompletionBackend(defaultBackendLabel);

        // Act
        var result = target.GetCompletionBackend(specificBackendLabel);

        // Assert
        Assert.IsType<OpenAIConfig>(result);
        Assert.Equal(specificBackendLabel, result.Label);
    }

    [Fact]
    public void GetCompletionBackendItReturnsDefaultWhenNoLabelIsProvided()
    {
        // Arrange
        var target = new KernelConfig();
        var defaultBackendLabel = "2";
        target.AddAzureOpenAICompletionBackend("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAICompletionBackend(defaultBackendLabel, "dep", "https://localhost", "key");
        target.SetDefaultCompletionBackend(defaultBackendLabel);

        // Act
        var result = target.GetCompletionBackend();

        // Assert
        Assert.IsType<AzureOpenAIConfig>(result);
        Assert.Equal(defaultBackendLabel, result.Label);
    }
}

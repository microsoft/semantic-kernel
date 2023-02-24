// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel.Configuration;
using Microsoft.SemanticKernel.Reliability;
using Moq;
using Xunit;

namespace SemanticKernelTests.Configuration;

/// <summary>
/// Unit tests of <see cref="KernelConfig"/>.
/// </summary>
public class KernelConfigTests
{
    [Fact]
    public void RetryMechanismIsSet()
    {
        // Arrange
        var retry = new PassThroughWithoutRetry();
        var config = new KernelConfig();

        // Act
        config.SetRetryMechanism(retry);

        // Assert
        Assert.Equal(retry, config.RetryMechanism);
    }

    [Fact]
    public void RetryMechanismIsSetWithCustomImplementation()
    {
        // Arrange
        var retry = new Mock<IRetryMechanism>();
        var config = new KernelConfig();

        // Act
        config.SetRetryMechanism(retry.Object);

        // Assert
        Assert.Equal(retry.Object, config.RetryMechanism);
    }

    [Fact]
    public void RetryMechanismIsSetToPassThroughWithoutRetryIfNull()
    {
        // Arrange
        var config = new KernelConfig();

        // Act
        config.SetRetryMechanism(null);

        // Assert
        Assert.IsType<PassThroughWithoutRetry>(config.RetryMechanism);
    }

    [Fact]
    public void RetryMechanismIsSetToPassThroughWithoutRetryIfNotSet()
    {
        // Arrange
        var config = new KernelConfig();

        // Act
        // Assert
        Assert.IsType<PassThroughWithoutRetry>(config.RetryMechanism);
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
            x => x.BackendType == BackendTypes.AzureOpenAI));
        Assert.False(target.HasCompletionBackend("azure",
            x => x.BackendType == BackendTypes.OpenAI));

        Assert.False(target.HasEmbeddingsBackend("oai2",
            x => x.BackendType == BackendTypes.AzureOpenAI));
        Assert.True(target.HasEmbeddingsBackend("oai2",
            x => x.BackendType == BackendTypes.OpenAI));

        Assert.True(target.HasCompletionBackend("azure",
            x => x.BackendType == BackendTypes.AzureOpenAI && x.AzureOpenAI?.DeploymentName == "depl"));
        Assert.False(target.HasCompletionBackend("azure",
            x => x.BackendType == BackendTypes.AzureOpenAI && x.AzureOpenAI?.DeploymentName == "nope"));
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
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace SemanticKernel.Connectors.HuggingFace.UnitTests;

public class HuggingFaceServiceCollectionExtensionsTests
{
    [Fact]
    public void AddHuggingFaceTextGenerationToServiceCollection()
    {
        var services = new ServiceCollection();
        services.AddHuggingFaceTextGeneration("model");

        var serviceProvider = services.BuildServiceProvider();
        var service = serviceProvider.GetRequiredService<ITextGenerationService>();

        Assert.NotNull(service);
        Assert.IsType<HuggingFaceTextGenerationService>(service);
    }

    [Fact]
    public void AddHuggingFaceEmbeddingGeneratorToServiceCollection()
    {
        var services = new ServiceCollection();
        services.AddHuggingFaceEmbeddingGenerator("model");

        var serviceProvider = services.BuildServiceProvider();
        var service = serviceProvider.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();

        Assert.NotNull(service);
        Assert.IsType<HuggingFaceEmbeddingGenerator>(service);
    }

    [Fact]
    [Obsolete("This test uses obsolete APIs. Use AddHuggingFaceEmbeddingGeneratorToServiceCollection instead.")]
    public void AddHuggingFaceTextEmbeddingsGenerationToServiceCollection()
    {
        var services = new ServiceCollection();
        services.AddHuggingFaceTextEmbeddingGeneration("model");

        var serviceProvider = services.BuildServiceProvider();
        var service = serviceProvider.GetRequiredService<ITextEmbeddingGenerationService>();

        Assert.NotNull(service);
        Assert.IsType<HuggingFaceTextEmbeddingGenerationService>(service);
    }
}

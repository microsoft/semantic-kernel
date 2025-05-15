// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace SemanticKernel.Connectors.HuggingFace.UnitTests;

public class HuggingFaceKernelBuilderExtensionsTests
{
    [Fact]
    public void AddHuggingFaceTextGenerationCreatesService()
    {
        var builder = Kernel.CreateBuilder();
        builder.AddHuggingFaceTextGeneration("model");

        var kernel = builder.Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();

        Assert.NotNull(kernel);
        Assert.NotNull(service);
        Assert.IsType<HuggingFaceTextGenerationService>(service);
    }

    [Fact]
    public void AddHuggingFaceEmbeddingGeneratorCreatesService()
    {
        var builder = Kernel.CreateBuilder();
        builder.AddHuggingFaceEmbeddingGenerator("model");

        var kernel = builder.Build();
        var service = kernel.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();

        Assert.NotNull(kernel);
        Assert.NotNull(service);
        Assert.IsType<HuggingFaceEmbeddingGenerator>(service);
    }

    [Fact]
    [Obsolete("This test uses obsolete APIs. Use AddHuggingFaceEmbeddingGeneratorCreatesService instead.")]
    public void AddHuggingFaceTextEmbeddingGenerationCreatesService()
    {
        var builder = Kernel.CreateBuilder();
        builder.AddHuggingFaceTextEmbeddingGeneration("model");

        var kernel = builder.Build();
        var service = kernel.GetRequiredService<ITextEmbeddingGenerationService>();

        Assert.NotNull(kernel);
        Assert.NotNull(service);
        Assert.IsType<HuggingFaceTextEmbeddingGenerationService>(service);
    }
}

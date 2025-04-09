// Copyright (c) Microsoft. All rights reserved.

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

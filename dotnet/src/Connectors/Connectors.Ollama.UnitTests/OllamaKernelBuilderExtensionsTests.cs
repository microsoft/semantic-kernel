// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Ollama;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace SemanticKernel.Connectors.Ollama.UnitTests;

public class OllamaKernelBuilderExtensionsTests
{
    [Fact]
    public void AddOllamaTextGenerationCreatesService()
    {
        var builder = Kernel.CreateBuilder();
        builder.AddOllamaTextGeneration("model", new Uri("http://localhost:11434"));

        var kernel = builder.Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();

        Assert.NotNull(kernel);
        Assert.NotNull(service);
        Assert.IsType<OllamaTextGenerationService>(service);
    }

    [Fact]
    public void AddOllamaChatCompletionCreatesService()
    {
        var builder = Kernel.CreateBuilder();
        builder.AddOllamaChatCompletion("model", new Uri("http://localhost:11434"));

        var kernel = builder.Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();

        Assert.NotNull(kernel);
        Assert.NotNull(service);
        Assert.IsType<OllamaChatCompletionService>(service);
    }

    [Fact]
    public void AddOllamaTextEmbeddingGenerationCreatesService()
    {
        var builder = Kernel.CreateBuilder();
        builder.AddOllamaTextEmbeddingGeneration("model", new Uri("http://localhost:11434"));

        var kernel = builder.Build();
        var service = kernel.GetRequiredService<ITextEmbeddingGenerationService>();

        Assert.NotNull(kernel);
        Assert.NotNull(service);
        Assert.IsType<OllamaTextEmbeddingGenerationService>(service);
    }
}

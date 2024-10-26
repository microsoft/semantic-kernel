// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Embeddings;
using Xunit;

namespace SemanticKernel.UnitTests.AI;

public class ServiceConversionExtensionsTests
{
    [Fact]
    public void InvalidArgumentsThrow()
    {
        Assert.Throws<ArgumentNullException>("service", () => ChatCompletionServiceExtensions.AsChatClient(null!));
        Assert.Throws<ArgumentNullException>("client", () => ChatCompletionServiceExtensions.AsChatCompletionService(null!));

        Assert.Throws<ArgumentNullException>("service", () => EmbeddingGenerationExtensions.AsEmbeddingGenerator<string, float>(null!));
        Assert.Throws<ArgumentNullException>("generator", () => EmbeddingGenerationExtensions.AsEmbeddingGenerationService<string, float>(null!));
    }
}

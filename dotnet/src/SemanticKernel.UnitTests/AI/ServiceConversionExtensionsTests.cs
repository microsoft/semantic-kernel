// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.AI;

public class ServiceConversionExtensionsTests
{
    [Fact]
    public void InvalidArgumentsThrow()
    {
        Assert.Throws<ArgumentNullException>("service", () => ServiceConversionExtensions.AsChatClient(null!));
        Assert.Throws<ArgumentNullException>("client", () => ServiceConversionExtensions.AsChatCompletionService(null!));

        Assert.Throws<ArgumentNullException>("service", () => ServiceConversionExtensions.AsEmbeddingGenerator<string, float>(null!));
        Assert.Throws<ArgumentNullException>("generator", () => ServiceConversionExtensions.AsEmbeddingGenerationService<string, float>(null!));
    }
}

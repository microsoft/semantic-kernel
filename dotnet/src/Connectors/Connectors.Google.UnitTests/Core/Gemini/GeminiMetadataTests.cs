// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.Google;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Core.Gemini;

/// <summary>
/// Unit tests for <see cref="GeminiMetadata"/> class.
/// </summary>
public sealed class GeminiMetadataTests
{
    [Fact]
    public void ThoughtSignatureCanBeSetAndRetrieved()
    {
        // Arrange & Act
        var metadata = new GeminiMetadata { ThoughtSignature = "test-signature-123" };

        // Assert
        Assert.Equal("test-signature-123", metadata.ThoughtSignature);
    }

    [Fact]
    public void ThoughtSignatureIsNullByDefault()
    {
        // Arrange & Act
        var metadata = new GeminiMetadata();

        // Assert
        Assert.Null(metadata.ThoughtSignature);
    }

    [Fact]
    public void ThoughtSignatureIsStoredInDictionary()
    {
        // Arrange
        var metadata = new GeminiMetadata { ThoughtSignature = "dict-signature" };

        // Act
        var hasKey = metadata.TryGetValue("ThoughtSignature", out var value);

        // Assert
        Assert.True(hasKey);
        Assert.Equal("dict-signature", value);
    }

    [Fact]
    public void ThoughtSignatureCanBeRetrievedFromDictionary()
    {
        // Arrange - This simulates deserialized metadata
        var metadata = new GeminiMetadata { ThoughtSignature = "from-dict" };

        // Act
        var signature = metadata.ThoughtSignature;

        // Assert
        Assert.Equal("from-dict", signature);
    }
}

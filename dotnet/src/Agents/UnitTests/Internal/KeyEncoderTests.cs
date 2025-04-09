// Copyright (c) Microsoft. All rights reserved.
using System.Linq;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Internal;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Internal;

/// <summary>
/// Unit testing of <see cref="KeyEncoder"/>.
/// </summary>
public class KeyEncoderTests
{
    /// <summary>
    /// Validate the production of unique and consistent hashes.
    /// </summary>
    [Fact]
    public void VerifyKeyEncoderUniqueness()
    {
        // Act
        this.VerifyHashEquivalancy([]);
        this.VerifyHashEquivalancy(nameof(KeyEncoderTests));
        this.VerifyHashEquivalancy(nameof(KeyEncoderTests), "http://localhost", "zoo");

        // Assert: Verify "well-known" value
        string localHash = KeyEncoder.GenerateHash([typeof(ChatHistoryChannel).FullName!]);
        Assert.Equal("Vdx37EnWT9BS+kkCkEgFCg9uHvHNw1+hXMA4sgNMKs4=", localHash);
    }

    private void VerifyHashEquivalancy(params string[] keys)
    {
        // Act
        string hash1 = KeyEncoder.GenerateHash(keys);
        string hash2 = KeyEncoder.GenerateHash(keys);
        string hash3 = KeyEncoder.GenerateHash(keys.Concat(["another"]));

        // Assert
        Assert.Equal(hash1, hash2);
        Assert.NotEqual(hash1, hash3);
    }
}

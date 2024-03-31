// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Linq;
using Microsoft.SemanticKernel.Agents.Internal;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Internal;

public class KeyEncoderTests
{
    [Fact]
    public void VerifyKeyEncoderUniquenessTest()
    {
        this.VerifyHashEquivalancy(Array.Empty<string>());
        this.VerifyHashEquivalancy(typeof(KeyEncoderTests).FullName);
        this.VerifyHashEquivalancy(typeof(KeyEncoderTests).FullName, "http://localhost", "zoo");
    }

    private void VerifyHashEquivalancy(params string[] keys)
    {
        string hash1 = KeyEncoder.GenerateHash(keys);
        string hash2 = KeyEncoder.GenerateHash(keys);
        string hash3 = KeyEncoder.GenerateHash(keys.Concat(["another"]));

        Assert.Equal(hash1, hash2);
        Assert.NotEqual(hash1, hash3);
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Connectors.Pinecone;
using Xunit;

namespace SemanticKernel.Connectors.Pinecone.UnitTests;

/// <summary>
/// Unit tests for PineconeClient class
/// </summary>
public sealed class PineconeClientTests
{
    [Theory]
    [InlineData("https://malicious-site.com")]
    [InlineData("http://internal-network.local")]
    [InlineData("ftp://attacker.com")]
    [InlineData("//bypass.com")]
    [InlineData("javascript:alert(1)")]
    [InlineData("data:text/html,<script>alert(1)</script>")]
    [Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
    public void ItThrowsOnEnvironmentUrlInjectionAttempt(string maliciousEnvironment)
    {
        // Arrange & Act & Assert
        Assert.Throws<ArgumentException>(() =>
        {
            var client = new PineconeClient(
                pineconeEnvironment: maliciousEnvironment,
                apiKey: "fake-api-key");
        });
    }

    [Theory]
    [InlineData("pinecone1")]
    [InlineData("pncn-starter")]
    [InlineData("us-east-1-pncn")]
    [InlineData("us-west-2-pncn")]
    [InlineData("asia-southeast-1-pncn")]
    [InlineData("eu-west-1-pncn")]
    [InlineData("northamerica-northeast1-pncn")]
    [Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
    public void ItAcceptsValidEnvironmentNames(string validEnvironment)
    {
        // Arrange & Act & Assert
        var exception = Record.Exception(() =>
        {
            var client = new PineconeClient(
                pineconeEnvironment: validEnvironment,
                apiKey: "fake-api-key");
        });

        Assert.Null(exception);
    }
}

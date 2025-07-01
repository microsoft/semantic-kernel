// Copyright (c) Microsoft. All rights reserved.

using FluentAssertions;
using Xunit;

namespace Microsoft.SemanticKernel.Agents.Runtime.Abstractions.Tests;

[Trait("Category", "Unit")]
public class AgentMetadataTests()
{
    [Fact]
    public void AgentMetadataShouldInitializeCorrectlyTest()
    {
        // Arrange & Act
        AgentMetadata metadata = new("TestType", "TestKey", "TestDescription");

        // Assert
        metadata.Type.Should().Be("TestType");
        metadata.Key.Should().Be("TestKey");
        metadata.Description.Should().Be("TestDescription");
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Agents;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Definition;

/// <summary>
/// Unit testing of <see cref="AgentDefinition"/> and related model classes.
/// </summary>
public class AgentDefinitionModelTests
{
    /// <summary>
    /// Verify ModelDefinition.Api cannot be null or whitespace.
    /// </summary>
    [Fact]
    public void VerifyModelDefinitionApiNotNullOrWhiteSpace()
    {
        // Arrange
        var modelDefinition = new ModelDefinition();

        // Act & Assert
        Assert.Throws<ArgumentException>(() => modelDefinition.Api = "");
        Assert.Throws<ArgumentNullException>(() => modelDefinition.Api = null!);
    }
}

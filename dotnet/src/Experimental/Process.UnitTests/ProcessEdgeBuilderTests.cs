// Copyright (c) Microsoft. All rights reserved.

using Xunit;

namespace Microsoft.SemanticKernel.UnitTests;

/// <summary>
/// Unit testing of <see cref="ProcessEdgeBuilder"/>.
/// </summary>
public class ProcessEdgeBuilderTests
{
    /// <summary>
    /// Verify initialization of <see cref="ProcessEdgeBuilder"/>.
    /// </summary>
    [Fact]
    public void ProcessEdgeBuilderInitialization()
    {
        // Arrange
        var processBuilder = new ProcessBuilder("TestProcess");

        // Act
        var edgeBuilder = new ProcessEdgeBuilder(processBuilder, "TestEvent");

        // Assert
        Assert.NotNull(edgeBuilder);
    }
}

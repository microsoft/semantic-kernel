// Copyright (c) Microsoft. All rights reserved.

using Xunit;
using Xunit.Sdk;

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

    /// <summary>
    /// Verify behavior of <see cref="ProcessEdgeBuilder.SendEventTo"/>.
    /// </summary>
    [Fact]
    public void SendEventToLinksToTarget()
    {
        // Arrange
        var processBuilder = new ProcessBuilder("TestProcess");
        var edgeBuilder = new ProcessEdgeBuilder(processBuilder, "TestEvent");
        var targetStepBuilder = new ProcessStepEdgeBuilder(processBuilder, "TargetEvent");

        // Act
        edgeBuilder.SendEventTo(targetStepBuilder);

        // Assert
        Assert.Single(processBuilder.Edges);
        Assert.Equal([targetStepBuilder], processBuilder.Edges["TestEvent"]);
    }
}

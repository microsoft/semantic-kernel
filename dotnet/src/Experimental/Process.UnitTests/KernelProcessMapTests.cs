// Copyright (c) Microsoft. All rights reserved.
using System;
using Xunit;

namespace Microsoft.SemanticKernel.Process.UnitTests;

/// <summary>
/// Unit testing of <see cref="KernelProcessMap"/>.
/// </summary>
public class KernelProcessMapTests
{
    /// <summary>
    /// Verify initialization.
    /// </summary>
    [Fact]
    public void KernelProcessMapStateInitialization()
    {
        // Arrange
        KernelProcessState processState = new("Operation", "vTest");
        KernelProcess process = new(processState, [], []);
        KernelProcessMapState state = new(nameof(KernelProcessMapStateInitialization), "vTest", Guid.NewGuid().ToString());

        // Act
        KernelProcessMap map = new(state, process, []);

        // Assert
        Assert.Equal(state, map.State);
        Assert.Equivalent(process, map.Operation);
        Assert.Empty(map.Edges);
    }

    /// <summary>
    /// Verify <see cref="KernelProcessMapState"/> requires a name and id
    /// </summary>
    [Fact]
    public void KernelProcessMapStateRequiredProperties()
    {
        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new KernelProcessMapState(name: null!, "vTest", "testid"));
        Assert.Throws<ArgumentNullException>(() => new KernelProcessMapState(name: "testname", null!, "testid"));
        Assert.Throws<ArgumentNullException>(() => new KernelProcessMapState("testname", "vTest", null!));
    }
}

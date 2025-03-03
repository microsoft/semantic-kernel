// Copyright (c) Microsoft. All rights reserved.
using System;
using Xunit;

namespace Microsoft.SemanticKernel.Process.UnitTests;

/// <summary>
/// Unit testing of <see cref="KernelProcessProxy"/>.
/// </summary>
public class KernelProcessProxyTests
{
    /// <summary>
    /// Verify initialization.
    /// </summary>
    [Fact]
    public void KernelProcessProxyStateInitialization()
    {
        // Arrange
        KernelProcessStepState state = new(nameof(KernelProcessProxyStateInitialization), "vTest", Guid.NewGuid().ToString());

        // Act
        KernelProcessProxy proxy = new(state, []);

        // Assert
        Assert.Equal(state, proxy.State);
        Assert.Empty(proxy.Edges);
    }

    /// <summary>
    /// Verify <see cref="KernelProcessStepState"/> requires a name and id
    /// </summary>
    [Fact]
    public void KernelProcessProxyStateRequiredProperties()
    {
        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new KernelProcessStepState(name: null!, "vTest", "testid"));
        Assert.Throws<ArgumentNullException>(() => new KernelProcessStepState(name: "testname", null!, "testid"));
        Assert.Throws<ArgumentNullException>(() => new KernelProcessProxy(new KernelProcessStepState("testname", "vTest", null!), []));
    }
}

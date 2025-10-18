// Copyright (c) Microsoft. All rights reserved.

using System;
using Xunit;

namespace Microsoft.SemanticKernel.Process.UnitTests;

/// <summary>
/// Unit testing of <see cref="KernelProcessState"/>.
/// </summary>
public class KernelProcessStateTests
{
    /// <summary>
    /// Verify initialization of <see cref="KernelProcessState"/>.
    /// </summary>
    [Fact]
    public void KernelProcessStateInitializationSetsPropertiesCorrectly()
    {
        // Arrange
        string name = "TestProcess";
        string id = "123";

        // Act
        KernelProcessState state = new(name, "v1", id);

        // Assert
        Assert.Equal(name, state.StepId);
        Assert.Equal(id, state.RunId);
    }

    /// <summary>
    /// Verify initialization of <see cref="KernelProcessState"/> with null id.
    /// </summary>
    [Fact]
    public void KernelProcessStateInitializationWithNullIdSucceeds()
    {
        // Arrange
        string name = "TestProcess";

        // Act
        KernelProcessState state = new(name, version: "v1");

        // Assert
        Assert.Equal(name, state.StepId);
        Assert.Null(state.RunId);
    }

    /// <summary>
    /// Verify initialization of <see cref="KernelProcessState"/> with null name throws.
    /// </summary>
    [Fact]
    public void KernelProcessStateInitializationWithNullNameThrows()
    {
        // Act & Assert
        var ex = Assert.Throws<ArgumentNullException>(() => new KernelProcessState(name: null!, version: "v1"));
    }

    /// <summary>
    /// Verify initialization of <see cref="KernelProcessState"/> with null version throws.
    /// </summary>
    [Fact]
    public void KernelProcessStateInitializationWithNullVersionThrows()
    {
        // Act & Assert
        var ex = Assert.Throws<ArgumentNullException>(() => new KernelProcessState(name: "stateName", version: null!));
    }
}

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
        KernelProcessState state = new(name, id);

        // Assert
        Assert.Equal(name, state.Name);
        Assert.Equal(id, state.Id);
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
        KernelProcessState state = new(name);

        // Assert
        Assert.Equal(name, state.Name);
        Assert.Null(state.Id);
    }

    /// <summary>
    /// Verify initialization of <see cref="KernelProcessState"/> with null name throws.
    /// </summary>
    [Fact]
    public void KernelProcessStateInitializationWithNullNameThrows()
    {
        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new KernelProcessState(name: null!));
    }
}

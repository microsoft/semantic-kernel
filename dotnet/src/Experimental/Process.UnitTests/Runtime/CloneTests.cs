// Copyright (c) Microsoft. All rights reserved.
using Xunit;

namespace Microsoft.SemanticKernel.Process.Runtime.UnitTests;

/// <summary>
/// Unit tests for the ability to clone:
/// - <see cref="KernelProcessStepState"/>.
/// - <see cref="KernelProcessStepInfo"/>.
/// - <see cref="KernelProcess"/>.
/// </summary>
public class CloneTests
{
    /// <summary>
    /// %%%
    /// </summary>
    [Fact]
    public void VerifyCloneStepStateTest()
    {
        // Arrange
        ProcessEvent source = new("test", new KernelProcessEvent { Id = "1" });

        // Act & Assert
    }

    /// <summary>
    /// %%%
    /// </summary>
    [Fact]
    public void VerifyCloneSingleStepTest()
    {
        // Arrange
        ProcessEvent source = new("test", new KernelProcessEvent { Id = "1" });

        // Act & Assert
    }

    /// <summary>
    /// %%%
    /// </summary>
    [Fact]
    public void VerifyCloneSingleProcessTest()
    {
        // Arrange
        ProcessEvent source = new("test", new KernelProcessEvent { Id = "1" });

        // Act & Assert
    }

    /// <summary>
    /// %%%
    /// </summary>
    [Fact]
    public void VerifyCloneNestedProcessTest()
    {
        // Arrange
        ProcessEvent source = new("test", new KernelProcessEvent { Id = "1" });

        // Act & Assert
    }
}

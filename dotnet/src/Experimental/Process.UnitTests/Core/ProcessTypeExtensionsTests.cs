// Copyright (c) Microsoft. All rights reserved.

using System;
using Xunit;

namespace Microsoft.SemanticKernel.Process.Core.UnitTests;

/// <summary>
/// Unit tests for the <see cref="ProcessTypeExtensions"/> class.
/// </summary>
public class ProcessTypeExtensionsTests
{
    private sealed class TestState { }
    private class TestStep : KernelProcessStep<TestState> { }
    private sealed class DerivedTestStep : TestStep { }
    private sealed class NonStep { }
    private sealed class NonGenericStep : KernelProcessStep { }

    /// <summary>
    /// Verify that TryGetSubtypeOfStatefulStep returns true and the correct type when the type is a direct subtype of KernelProcessStep.
    /// </summary>
    [Fact]
    public void TryGetSubtypeOfStatefulStepDirectSubtypeReturnsTrue()
    {
        // Arrange
        Type type = typeof(TestStep);

        // Act
        bool result = type.TryGetSubtypeOfStatefulStep(out Type? genericStateType);

        // Assert
        Assert.True(result);
        Assert.NotNull(genericStateType);
        Assert.Equal(typeof(KernelProcessStep<TestState>), genericStateType);
    }

    /// <summary>
    /// Verify that TryGetSubtypeOfStatefulStep returns true and the correct type when the type is a subtype of a subtype of KernelProcessStep.
    /// </summary>
    [Fact]
    public void TryGetSubtypeOfStatefulStepInheritedSubtypeReturnsTrue()
    {
        // Arrange
        Type type = typeof(DerivedTestStep);

        // Act
        bool result = type.TryGetSubtypeOfStatefulStep(out Type? genericStateType);

        // Assert
        Assert.True(result);
        Assert.NotNull(genericStateType);
        Assert.Equal(typeof(KernelProcessStep<TestState>), genericStateType);
    }

    /// <summary>
    /// Verify that TryGetSubtypeOfStatefulStep returns false when the type is not a subtype of KernelProcessStep.
    /// </summary>
    [Fact]
    public void TryGetSubtypeOfStatefulStepNotASubtypeReturnsFalse()
    {
        // Arrange
        Type type = typeof(NonStep);

        // Act
        bool result = type.TryGetSubtypeOfStatefulStep(out Type? genericStateType);

        // Assert
        Assert.False(result);
        Assert.Null(genericStateType);
    }

    /// <summary>
    /// Verify that TryGetSubtypeOfStatefulStep returns false when the type is not a subtype of KernelProcessStep.
    /// </summary>
    [Fact]
    public void TryGetSubtypeOfStatefulStepNotAGenericSubtypeReturnsFalse()
    {
        // Arrange
        Type type = typeof(NonGenericStep);

        // Act
        bool result = type.TryGetSubtypeOfStatefulStep(out Type? genericStateType);

        // Assert
        Assert.False(result);
        Assert.Null(genericStateType);
    }

    /// <summary>
    /// Verify that TryGetSubtypeOfStatefulStep returns false when the type is null.
    /// </summary>
    [Fact]
    public void TryGetSubtypeOfStatefulStepNullTypeReturnsFalse()
    {
        // Arrange
        Type? type = null;

        // Act
        bool result = type.TryGetSubtypeOfStatefulStep(out Type? genericStateType);

        // Assert
        Assert.False(result);
        Assert.Null(genericStateType);
    }
}

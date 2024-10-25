// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel.Process.Internal;
using Xunit;

namespace SemanticKernel.Process.Utilities.UnitTests;

/// <summary>
/// Unit tests for the SharedPlaceholder class.
/// </summary>
public class PlaceholderTests
{
    /// <summary>
    /// Demonstrate a shared component can be tested.
    /// </summary>
    [Fact]
    public void VerifyInternalComponentTestable()
    {
        // Arrange, Act & Assert
        SharedPlaceholder.InjectedMethodDependency();
    }
}

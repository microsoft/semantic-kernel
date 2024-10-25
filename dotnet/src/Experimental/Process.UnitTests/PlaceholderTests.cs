// Copyright (c) Microsoft. All rights reserved.
//using Microsoft.SemanticKernel.Process.Internal;
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
        // Uncomment this to observe amibiguous type resolution (due to the internal visibility to the target projects).
        //SharedPlaceholder.InjectedMethodDependency();
    }
}

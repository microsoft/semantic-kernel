// Copyright (c) Microsoft. All rights reserved.
using System;
using Microsoft.SemanticKernel.Agents.Chat;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.Chat;

/// <summary>
/// Unit testing of <see cref="SelectionStrategy"/>.
/// </summary>
public class SelectionStrategyTests
{
    /// <summary>
    /// Verify <see cref="SelectionStrategy"/> is able to cast to <see cref="SelectionCriteriaCallback"/>.
    /// </summary>
    [Fact]
    public void VerifySelectionStrategyCastAsCriteriaCallback()
    {
        Mock<SelectionStrategy> strategyMock = new();
        try
        {
            SelectionCriteriaCallback callback = (SelectionCriteriaCallback)strategyMock.Object;
        }
        catch (InvalidCastException exception)
        {
            Assert.Fail($"Unable to cast strategy as criteria callback: {exception.Message}");
        }
    }
}

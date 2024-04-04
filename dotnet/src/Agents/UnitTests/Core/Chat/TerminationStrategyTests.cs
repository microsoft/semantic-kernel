// Copyright (c) Microsoft. All rights reserved.
using System;
using Microsoft.SemanticKernel.Agents.Chat;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.Chat;

/// <summary>
/// Unit testing of <see cref="TerminationStrategy"/>.
/// </summary>
public class TerminationStrategyTests
{
    /// <summary>
    /// Verify <see cref="TerminationStrategy"/> is able to cast to <see cref="TerminationCriteriaCallback"/>.
    /// </summary>
    [Fact]
    public void VerifySelectionStrategyCastAsCriteriaCallback()
    {
        Mock<TerminationStrategy> strategyMock = new();
        try
        {
            TerminationCriteriaCallback callback = (TerminationCriteriaCallback)strategyMock.Object;
        }
        catch (InvalidCastException exception)
        {
            Assert.Fail($"Unable to cast strategy as criteria callback: {exception.Message}");
        }
    }
}

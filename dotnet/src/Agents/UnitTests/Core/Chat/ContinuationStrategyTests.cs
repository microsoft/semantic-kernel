// Copyright (c) Microsoft. All rights reserved.
using System;
using Microsoft.SemanticKernel.Agents.Chat;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.Chat;

/// <summary>
/// Unit testing of <see cref="ContinuationStrategy"/>.
/// </summary>
public class ContinuationStrategyTests
{
    /// <summary>
    /// Verify <see cref="ContinuationStrategy"/> is able to cast to <see cref="ContinuationCriteriaCallback"/>.
    /// </summary>
    [Fact]
    public void VerifySelectionStrategyCastAsCriteriaCallback()
    {
        Mock<ContinuationStrategy> strategy = new();
        try
        {
            ContinuationCriteriaCallback callback = (ContinuationCriteriaCallback)strategy.Object;
        }
        catch (InvalidCastException exception)
        {
            Assert.Fail($"Unable to cast strategy as criteria callback: {exception.Message}");
        }
    }
}

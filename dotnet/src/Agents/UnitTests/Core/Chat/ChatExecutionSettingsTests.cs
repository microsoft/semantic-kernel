// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel.Agents.Chat;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.Chat;

/// <summary>
/// Unit testing of <see cref="ChatExecutionSettings"/>.
/// </summary>
public class ChatExecutionSettingsTests
{
    /// <summary>
    /// Verify default state.
    /// </summary>
    [Fact]
    public void VerifyChatExecutionSettingsDefault()
    {
        ChatExecutionSettings settings = new();
        Assert.Null(settings.ContinuationStrategy);
        Assert.Equal(ChatExecutionSettings.DefaultMaximumIterations, settings.MaximumIterations);
        Assert.Null(settings.SelectionStrategy);
    }

    /// <summary>
    /// Verify accepts <see cref="ContinuationStrategy"/> for <see cref="ChatExecutionSettings.ContinuationStrategy"/>.
    /// </summary>
    [Fact]
    public void VerifyChatExecutionContinuationStrategyDefault()
    {
        Mock<ContinuationStrategy> strategyMock = new();
        ChatExecutionSettings settings =
            new()
            {
                ContinuationStrategy = strategyMock.Object
            };
        Assert.NotNull(settings.ContinuationStrategy);
    }

    /// <summary>
    /// Verify accepts <see cref="SelectionStrategy"/> for <see cref="ChatExecutionSettings.SelectionStrategy"/>.
    /// </summary>
    [Fact]
    public void VerifyChatExecutionSelectionStrategyDefault()
    {
        Mock<SelectionStrategy> strategyMock = new();
        ChatExecutionSettings settings =
            new()
            {
                SelectionStrategy = strategyMock.Object
            };
        Assert.NotNull(settings.SelectionStrategy);
    }
}

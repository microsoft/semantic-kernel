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
        Assert.IsType<DefaultTerminationStrategy>(settings.TerminationStrategy);
        Assert.Equal(TerminationStrategy.DefaultMaximumIterations, settings.TerminationStrategy.MaximumIterations);
        Assert.Null(settings.SelectionStrategy);
    }

    /// <summary>
    /// Verify accepts <see cref="TerminationStrategy"/> for <see cref="ChatExecutionSettings.TerminationStrategy"/>.
    /// </summary>
    [Fact]
    public void VerifyChatExecutionContinuationStrategyDefault()
    {
        Mock<TerminationStrategy> strategyMock = new();
        ChatExecutionSettings settings =
            new()
            {
                TerminationStrategy = strategyMock.Object
            };

        Assert.Equal(strategyMock.Object, settings.TerminationStrategy);
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
        Assert.Equal(strategyMock.Object, settings.SelectionStrategy);
    }
}

// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel.Agents.Chat;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.Chat;

/// <summary>
/// Unit testing of <see cref="AgentGroupChatSettings"/>.
/// </summary>
public class AgentGroupChatSettingsTests
{
    /// <summary>
    /// Verify default state.
    /// </summary>
    [Fact]
    public void VerifyChatExecutionSettingsDefault()
    {
        // Arrange
        AgentGroupChatSettings settings = new();

        // Assert
        Assert.IsType<AgentGroupChatSettings.DefaultTerminationStrategy>(settings.TerminationStrategy);
        Assert.Equal(1, settings.TerminationStrategy.MaximumIterations);
        Assert.IsType<SequentialSelectionStrategy>(settings.SelectionStrategy);
    }

    /// <summary>
    /// Verify accepts <see cref="TerminationStrategy"/> for <see cref="AgentGroupChatSettings.TerminationStrategy"/>.
    /// </summary>
    [Fact]
    public void VerifyChatExecutionContinuationStrategyDefault()
    {
        // Arrange
        Mock<TerminationStrategy> strategyMock = new();
        AgentGroupChatSettings settings =
            new()
            {
                TerminationStrategy = strategyMock.Object
            };

        // Assert
        Assert.Equal(strategyMock.Object, settings.TerminationStrategy);
    }

    /// <summary>
    /// Verify accepts <see cref="SelectionStrategy"/> for <see cref="AgentGroupChatSettings.SelectionStrategy"/>.
    /// </summary>
    [Fact]
    public void VerifyChatExecutionSelectionStrategyDefault()
    {
        // Arrange
        Mock<SelectionStrategy> strategyMock = new();
        AgentGroupChatSettings settings =
            new()
            {
                SelectionStrategy = strategyMock.Object
            };

        // Assert
        Assert.NotNull(settings.SelectionStrategy);
        Assert.Equal(strategyMock.Object, settings.SelectionStrategy);
    }
}

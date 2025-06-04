// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using OpenAI.Assistants;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Tests for <see cref="OpenAIAssistantAgentInvokeOptions"/>.
/// </summary>
public class OpenAIAssistantAgentInvokeOptionsTests
{
    /// <summary>
    /// Tests the constructor of <see cref="OpenAIAssistantAgentInvokeOptions"/> to ensure it correctly clones properties from the base class.
    /// </summary>
    [Fact]
    public void ConstructorShouldClonePropertiesCorrectly()
    {
        // Arrange
        var originalOptions = new OpenAIAssistantAgentInvokeOptions
        {
            RunCreationOptions = new RunCreationOptions(),
            AdditionalInstructions = "Test instructions"
        };

        // Act
        var clonedOptions = new OpenAIAssistantAgentInvokeOptions(originalOptions);

        // Assert
        Assert.NotNull(clonedOptions.RunCreationOptions);
        Assert.Equal(originalOptions.RunCreationOptions, clonedOptions.RunCreationOptions);
        Assert.Equal(originalOptions.AdditionalInstructions, clonedOptions.AdditionalInstructions);
    }

    /// <summary>
    /// Tests the constructor of <see cref="OpenAIAssistantAgentInvokeOptions"/> to ensure it correctly clones properties from an instance of <see cref="AgentInvokeOptions"/>.
    /// </summary>
    [Fact]
    public void ConstructorShouldCloneAgentInvokeOptionsPropertiesCorrectly()
    {
        // Arrange
        var originalOptions = new AgentInvokeOptions
        {
            AdditionalInstructions = "Test instructions"
        };

        // Act
        var clonedOptions = new OpenAIAssistantAgentInvokeOptions(originalOptions);

        // Assert
        Assert.Equal(originalOptions.AdditionalInstructions, clonedOptions.AdditionalInstructions);
    }
}

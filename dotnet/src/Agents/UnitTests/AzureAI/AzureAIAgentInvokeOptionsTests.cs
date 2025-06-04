// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.AzureAI;

/// <summary>
/// Tests for <see cref="AzureAIAgentInvokeOptions"/>.
/// </summary>
public class AzureAIAgentInvokeOptionsTests
{
    /// <summary>
    /// Tests the constructor of <see cref="AzureAIAgentInvokeOptions"/> to ensure it correctly clones properties from the base class.
    /// </summary>
    [Fact]
    public void ConstructorShouldClonePropertiesCorrectly()
    {
        // Arrange
        var originalOptions = new AzureAIAgentInvokeOptions
        {
            ModelName = "TestModel",
            AdditionalMessages = new List<ChatMessageContent>(),
            EnableCodeInterpreter = true,
            EnableFileSearch = true,
            EnableJsonResponse = true,
            MaxCompletionTokens = 100,
            MaxPromptTokens = 50,
            ParallelToolCallsEnabled = true,
            TruncationMessageCount = 10,
            Temperature = 0.5f,
            TopP = 0.9f,
            Metadata = new Dictionary<string, string> { { "key", "value" } }
        };

        // Act
        var clonedOptions = new AzureAIAgentInvokeOptions(originalOptions);

        // Assert
        Assert.Equal(originalOptions.ModelName, clonedOptions.ModelName);
        Assert.Equal(originalOptions.AdditionalMessages, clonedOptions.AdditionalMessages);
        Assert.Equal(originalOptions.EnableCodeInterpreter, clonedOptions.EnableCodeInterpreter);
        Assert.Equal(originalOptions.EnableFileSearch, clonedOptions.EnableFileSearch);
        Assert.Equal(originalOptions.EnableJsonResponse, clonedOptions.EnableJsonResponse);
        Assert.Equal(originalOptions.MaxCompletionTokens, clonedOptions.MaxCompletionTokens);
        Assert.Equal(originalOptions.MaxPromptTokens, clonedOptions.MaxPromptTokens);
        Assert.Equal(originalOptions.ParallelToolCallsEnabled, clonedOptions.ParallelToolCallsEnabled);
        Assert.Equal(originalOptions.TruncationMessageCount, clonedOptions.TruncationMessageCount);
        Assert.Equal(originalOptions.Temperature, clonedOptions.Temperature);
        Assert.Equal(originalOptions.TopP, clonedOptions.TopP);
        Assert.Equal(originalOptions.Metadata, clonedOptions.Metadata);
    }

    /// <summary>
    /// Tests the constructor of <see cref="AzureAIAgentInvokeOptions"/> to ensure it correctly clones properties from an instance of <see cref="AgentInvokeOptions"/>.
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
        var clonedOptions = new AzureAIAgentInvokeOptions(originalOptions);

        // Assert
        Assert.Equal(originalOptions.AdditionalInstructions, clonedOptions.AdditionalInstructions);
    }
}

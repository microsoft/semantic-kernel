// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.Agents.OpenAI.Internal;
using Moq;
using OpenAI.Responses;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI.Internal;

/// <summary>
/// Unit testing of <see cref="ResponseCreationOptionsFactory"/>.
/// </summary>
public class ResponseCreationOptionsFactoryTests
{
    /// <summary>
    /// Verify response options creation with null invoke options.
    /// </summary>
    [Fact]
    public void CreateOptionsWithNullInvokeOptionsTest()
    {
        // Arrange
        var mockAgent = CreateMockAgent("Test Agent", "You are a helpful assistant.", storeEnabled: false);
        var mockThread = CreateMockAgentThread(null);

        // Act
        var options = ResponseCreationOptionsFactory.CreateOptions(mockAgent, mockThread.Object, null);

        // Assert
        Assert.NotNull(options);
        Assert.Equal("Test Agent", options.EndUserId);
        Assert.Equal("You are a helpful assistant.", options.Instructions);
        Assert.False(options.StoredOutputEnabled);
        Assert.Null(options.ReasoningOptions);
        Assert.Null(options.MaxOutputTokenCount);
        Assert.Null(options.TextOptions);
        Assert.Null(options.TruncationMode);
        Assert.Null(options.ParallelToolCallsEnabled);
        Assert.Null(options.ToolChoice);
        Assert.Empty(options.Tools);
        Assert.Null(options.PreviousResponseId);
    }

    /// <summary>
    /// Verify response options creation with store enabled and thread ID.
    /// </summary>
    [Fact]
    public void CreateOptionsWithStoreEnabledAndThreadIdTest()
    {
        // Arrange
        var mockAgent = CreateMockAgent("Test Agent", "You are a helpful assistant.", storeEnabled: true);
        var mockThread = CreateMockAgentThread("thread-123");

        // Act
        var options = ResponseCreationOptionsFactory.CreateOptions(mockAgent, mockThread.Object, null);

        // Assert
        Assert.NotNull(options);
        Assert.Equal("Test Agent", options.EndUserId);
        Assert.Equal("You are a helpful assistant.", options.Instructions);
        Assert.True(options.StoredOutputEnabled);
        Assert.Equal("thread-123", options.PreviousResponseId);
    }

    /// <summary>
    /// Verify response options creation with additional instructions from invoke options.
    /// </summary>
    [Fact]
    public void CreateOptionsWithAdditionalInstructionsTest()
    {
        // Arrange
        var mockAgent = CreateMockAgent("Test Agent", "You are a helpful assistant.", storeEnabled: false);
        var mockThread = CreateMockAgentThread(null);
        var invokeOptions = new AgentInvokeOptions
        {
            AdditionalInstructions = "Be more concise."
        };

        // Act
        var options = ResponseCreationOptionsFactory.CreateOptions(mockAgent, mockThread.Object, invokeOptions);

        // Assert
        Assert.NotNull(options);
        Assert.Equal("Test Agent", options.EndUserId);
        Assert.Equal("You are a helpful assistant.\nBe more concise.", options.Instructions);
        Assert.False(options.StoredOutputEnabled);
    }

    /// <summary>
    /// Verify response options creation with OpenAIResponseAgentInvokeOptions with full ResponseCreationOptions.
    /// </summary>
    [Fact]
    public void CreateOptionsWithResponseAgentInvokeOptionsTest()
    {
        // Arrange
        var mockAgent = CreateMockAgent("Test Agent", "You are a helpful assistant.", storeEnabled: false);
        var mockThread = CreateMockAgentThread(null);
        var responseCreationOptions = new ResponseCreationOptions
        {
            EndUserId = "custom-user",
            Instructions = "Custom instructions",
            StoredOutputEnabled = true,
            MaxOutputTokenCount = 1000,
            ParallelToolCallsEnabled = true,
            ToolChoice = ResponseToolChoice.CreateAutoChoice(),
            Temperature = 0.7f,
            TopP = 0.9f,
            PreviousResponseId = "previous-response-id",
        };
        responseCreationOptions.Tools.Add(ResponseTool.CreateWebSearchTool());

        var invokeOptions = new OpenAIResponseAgentInvokeOptions
        {
            AdditionalInstructions = "Additional instructions",
            ResponseCreationOptions = responseCreationOptions
        };

        // Act
        var options = ResponseCreationOptionsFactory.CreateOptions(mockAgent, mockThread.Object, invokeOptions);

        // Assert
        Assert.NotNull(options);
        Assert.Equal("custom-user", options.EndUserId);
        Assert.Equal("Custom instructions", options.Instructions);
        Assert.True(options.StoredOutputEnabled);
        Assert.Equal(1000, options.MaxOutputTokenCount);
        Assert.True(options.ParallelToolCallsEnabled);
        Assert.NotNull(options.ToolChoice);
        Assert.Single(options.Tools);
        Assert.Equal(0.7f, options.Temperature);
        Assert.Equal(0.9f, options.TopP);
        Assert.Equal("previous-response-id", options.PreviousResponseId);
    }

    /// <summary>
    /// Verify response options creation with ResponseCreationOptions having null values that fallback to agent defaults.
    /// </summary>
    [Fact]
    public void CreateOptionsWithResponseCreationOptionsNullFallbackTest()
    {
        // Arrange
        var mockAgent = CreateMockAgent("Test Agent", "You are a helpful assistant.", storeEnabled: true);
        var mockThread = CreateMockAgentThread(null);
        var responseCreationOptions = new ResponseCreationOptions
        {
            EndUserId = null, // Should fallback to agent display name
            Instructions = null, // Should fallback to agent instructions + additional
            StoredOutputEnabled = null // Should fallback to agent store enabled
        };

        var invokeOptions = new OpenAIResponseAgentInvokeOptions
        {
            AdditionalInstructions = "Be helpful",
            ResponseCreationOptions = responseCreationOptions
        };

        // Act
        var options = ResponseCreationOptionsFactory.CreateOptions(mockAgent, mockThread.Object, invokeOptions);

        // Assert
        Assert.NotNull(options);
        Assert.Equal("Test Agent", options.EndUserId);
        Assert.Equal("You are a helpful assistant.\nBe helpful", options.Instructions);
        Assert.True(options.StoredOutputEnabled);
    }

    /// <summary>
    /// Verify response options creation when agent has null instructions.
    /// </summary>
    [Fact]
    public void CreateOptionsWithNullAgentInstructionsTest()
    {
        // Arrange
        var mockAgent = CreateMockAgent("Test Agent", null, storeEnabled: false);
        var mockThread = CreateMockAgentThread(null);

        var invokeOptions = new AgentInvokeOptions
        {
            AdditionalInstructions = "Be helpful"
        };

        // Act
        var options = ResponseCreationOptionsFactory.CreateOptions(mockAgent, mockThread.Object, invokeOptions);

        // Assert
        Assert.NotNull(options);
        Assert.Equal("Be helpful", options.Instructions);
    }

    /// <summary>
    /// Verify response options creation when both agent instructions and additional instructions are null.
    /// </summary>
    [Fact]
    public void CreateOptionsWithAllNullInstructionsTest()
    {
        // Arrange
        var mockAgent = CreateMockAgent("Test Agent", null, storeEnabled: false);
        var mockThread = CreateMockAgentThread(null);

        // Act
        var options = ResponseCreationOptionsFactory.CreateOptions(mockAgent, mockThread.Object, null);

        // Assert
        Assert.NotNull(options);
        Assert.Equal("", options.Instructions);
    }

    /// <summary>
    /// Verify response options creation when agent store is disabled but thread ID exists.
    /// </summary>
    [Fact]
    public void CreateOptionsWithStoreDisabledButThreadIdExistsTest()
    {
        // Arrange
        var mockAgent = CreateMockAgent("Test Agent", "You are a helpful assistant.", storeEnabled: false);
        var mockThread = CreateMockAgentThread("thread-123");

        // Act
        var options = ResponseCreationOptionsFactory.CreateOptions(mockAgent, mockThread.Object, null);

        // Assert
        Assert.NotNull(options);
        Assert.False(options.StoredOutputEnabled);
        Assert.Null(options.PreviousResponseId); // Should not set previous response ID when store is disabled
    }

    /// <summary>
    /// Verify response options creation with empty agent name fallback to "UnnamedAgent".
    /// </summary>
    [Fact]
    public void CreateOptionsWithEmptyAgentNameTest()
    {
        // Arrange
        var mockAgent = CreateMockAgent("", "You are a helpful assistant.", storeEnabled: false);
        var mockThread = CreateMockAgentThread(null);

        // Act
        var options = ResponseCreationOptionsFactory.CreateOptions(mockAgent, mockThread.Object, null);

        // Assert
        Assert.NotNull(options);
        Assert.Equal("UnnamedAgent", options.EndUserId); // Empty name should fallback to "UnnamedAgent"
    }

    /// <summary>
    /// Verify response options creation with null agent name fallback to "UnnamedAgent".
    /// </summary>
    [Fact]
    public void CreateOptionsWithNullAgentNameTest()
    {
        // Arrange
        var mockAgent = CreateMockAgent(null, "You are a helpful assistant.", storeEnabled: false);
        var mockThread = CreateMockAgentThread(null);

        // Act
        var options = ResponseCreationOptionsFactory.CreateOptions(mockAgent, mockThread.Object, null);

        // Assert
        Assert.NotNull(options);
        Assert.Equal("UnnamedAgent", options.EndUserId); // Null name should fallback to "UnnamedAgent"
    }

    private static OpenAIResponseAgent CreateMockAgent(string? name, string? instructions, bool storeEnabled)
    {
        var mockClient = new Mock<OpenAIResponseClient>();
        var mockAgent = new OpenAIResponseAgent(mockClient.Object)
        {
            Name = name ?? "UnnamedAgent",
            Instructions = instructions ?? string.Empty,
            StoreEnabled = storeEnabled,
            Kernel = new Kernel() // Empty kernel for testing
        };

        return mockAgent;
    }

    private static Mock<AgentThread> CreateMockAgentThread(string? threadId)
    {
        var mockThread = new Mock<AgentThread>();
        mockThread.Setup(t => t.Id).Returns(threadId);
        return mockThread;
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Amazon.UnitTests;

/// <summary>
/// Unit tests for BedrockModelUtilities, specifically the BuildMessageList method
/// and its handling of tool call / tool result merging.
/// </summary>
public sealed class BedrockModelUtilitiesTests
{
    /// <summary>
    /// Verifies that simple text messages are converted correctly.
    /// </summary>
    [Fact]
    public void BuildMessageListShouldConvertSimpleTextMessages()
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");
        chatHistory.AddAssistantMessage("Hi there");
        chatHistory.AddUserMessage("How are you?");

        // Act
        var messages = Core.BedrockModelUtilities.BuildMessageList(chatHistory);

        // Assert
        Assert.Equal(3, messages.Count);
        Assert.Equal(ConversationRole.User, messages[0].Role);
        Assert.Equal("Hello", messages[0].Content[0].Text);
        Assert.Equal(ConversationRole.Assistant, messages[1].Role);
        Assert.Equal("Hi there", messages[1].Content[0].Text);
        Assert.Equal(ConversationRole.User, messages[2].Role);
        Assert.Equal("How are you?", messages[2].Content[0].Text);
    }

    /// <summary>
    /// Verifies that system messages are excluded from the message list.
    /// </summary>
    [Fact]
    public void BuildMessageListShouldExcludeSystemMessages()
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddSystemMessage("You are an AI assistant");
        chatHistory.AddUserMessage("Hello");

        // Act
        var messages = Core.BedrockModelUtilities.BuildMessageList(chatHistory);

        // Assert
        Assert.Single(messages);
        Assert.Equal(ConversationRole.User, messages[0].Role);
        Assert.Equal("Hello", messages[0].Content[0].Text);
    }

    /// <summary>
    /// Verifies that consecutive assistant messages with FunctionCallContent are merged into a single message.
    /// This is the core scenario from issue #13647.
    /// </summary>
    [Fact]
    public void BuildMessageListShouldMergeConsecutiveAssistantToolCalls()
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Get feeds and distribution list");

        // First assistant message with a tool call
        var assistantMessage1 = new ChatMessageContent(AuthorRole.Assistant, (string?)null);
        assistantMessage1.Items.Add(new FunctionCallContent(
            functionName: "GetFeeds",
            pluginName: "Feeds",
            id: "tooluse_G64hibpFmRqXEcAYwOfP5s"));
        chatHistory.Add(assistantMessage1);

        // Second assistant message with another tool call (parallel tool invocation)
        var assistantMessage2 = new ChatMessageContent(AuthorRole.Assistant, (string?)null);
        assistantMessage2.Items.Add(new FunctionCallContent(
            functionName: "GetTeamsDistributionList",
            pluginName: "DistributionList",
            id: "tooluse_sMmlRWbbCGd0lnhiLjvk8H",
            arguments: new KernelArguments { { "distributionListName", "developers" } }));
        chatHistory.Add(assistantMessage2);

        // Act
        var messages = Core.BedrockModelUtilities.BuildMessageList(chatHistory);

        // Assert
        Assert.Equal(2, messages.Count); // user + single merged assistant

        // The assistant message should have been merged
        var assistantMsg = messages[1];
        Assert.Equal(ConversationRole.Assistant, assistantMsg.Role);
        Assert.Equal(2, assistantMsg.Content.Count);

        // First tool use
        Assert.NotNull(assistantMsg.Content[0].ToolUse);
        Assert.Equal("tooluse_G64hibpFmRqXEcAYwOfP5s", assistantMsg.Content[0].ToolUse.ToolUseId);
        Assert.Equal("Feeds-GetFeeds", assistantMsg.Content[0].ToolUse.Name);

        // Second tool use
        Assert.NotNull(assistantMsg.Content[1].ToolUse);
        Assert.Equal("tooluse_sMmlRWbbCGd0lnhiLjvk8H", assistantMsg.Content[1].ToolUse.ToolUseId);
        Assert.Equal("DistributionList-GetTeamsDistributionList", assistantMsg.Content[1].ToolUse.Name);
    }

    /// <summary>
    /// Verifies that consecutive tool result messages are merged into a single user message.
    /// This is part of the scenario from issue #13647.
    /// </summary>
    [Fact]
    public void BuildMessageListShouldMergeConsecutiveToolResults()
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Get feeds and distribution list");

        // Assistant with tool calls (single message with multiple items)
        var assistantMessage = new ChatMessageContent(AuthorRole.Assistant, (string?)null);
        assistantMessage.Items.Add(new FunctionCallContent(
            functionName: "GetFeeds",
            pluginName: "Feeds",
            id: "tooluse_G64hibpFmRqXEcAYwOfP5s"));
        assistantMessage.Items.Add(new FunctionCallContent(
            functionName: "GetTeamsDistributionList",
            pluginName: "DistributionList",
            id: "tooluse_sMmlRWbbCGd0lnhiLjvk8H",
            arguments: new KernelArguments { { "distributionListName", "developers" } }));
        chatHistory.Add(assistantMessage);

        // First tool result
        var toolResult1 = new ChatMessageContent(AuthorRole.Tool, (string?)null);
        toolResult1.Items.Add(new FunctionResultContent(
            functionName: "GetFeeds",
            pluginName: "Feeds",
            callId: "tooluse_G64hibpFmRqXEcAYwOfP5s",
            result: "Dataset DataReference: memory://8df2be02a23c4ebfb77e1170dea6c4b4. Dataset size: 78 items."));
        chatHistory.Add(toolResult1);

        // Second tool result
        var toolResult2 = new ChatMessageContent(AuthorRole.Tool, (string?)null);
        toolResult2.Items.Add(new FunctionResultContent(
            functionName: "GetTeamsDistributionList",
            pluginName: "DistributionList",
            callId: "tooluse_sMmlRWbbCGd0lnhiLjvk8H",
            result: "19:791df3464b4f4c3fac8429041e8e2540@thread.v2"));
        chatHistory.Add(toolResult2);

        // Act
        var messages = Core.BedrockModelUtilities.BuildMessageList(chatHistory);

        // Assert
        Assert.Equal(3, messages.Count); // user + assistant + single merged tool results (as user)

        // Tool results should be merged into a single user message
        var toolResultMsg = messages[2];
        Assert.Equal(ConversationRole.User, toolResultMsg.Role); // Tool role maps to User in Bedrock
        Assert.Equal(2, toolResultMsg.Content.Count);

        // First tool result
        Assert.NotNull(toolResultMsg.Content[0].ToolResult);
        Assert.Equal("tooluse_G64hibpFmRqXEcAYwOfP5s", toolResultMsg.Content[0].ToolResult.ToolUseId);
        Assert.Equal("Dataset DataReference: memory://8df2be02a23c4ebfb77e1170dea6c4b4. Dataset size: 78 items.",
            toolResultMsg.Content[0].ToolResult.Content[0].Text);

        // Second tool result
        Assert.NotNull(toolResultMsg.Content[1].ToolResult);
        Assert.Equal("tooluse_sMmlRWbbCGd0lnhiLjvk8H", toolResultMsg.Content[1].ToolResult.ToolUseId);
        Assert.Equal("19:791df3464b4f4c3fac8429041e8e2540@thread.v2",
            toolResultMsg.Content[1].ToolResult.Content[0].Text);
    }

    /// <summary>
    /// Full round-trip test matching the exact scenario from issue #13647:
    /// separate assistant tool-call messages + separate tool-result messages.
    /// After merging, the Bedrock message list should have properly coalesced messages.
    /// </summary>
    [Fact]
    public void BuildMessageListShouldProduceValidBedrockMessagesForParallelToolCalls()
    {
        // Arrange: Reproduce the exact ChatHistory from the issue
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Audit the feeds and get the developers distribution list");

        // Two separate assistant messages with tool calls (as SK creates them)
        var assistantMsg1 = new ChatMessageContent(AuthorRole.Assistant, (string?)null);
        assistantMsg1.Items.Add(new FunctionCallContent(
            functionName: "GetFeeds",
            pluginName: "Feeds",
            id: "tooluse_G64hibpFmRqXEcAYwOfP5s"));
        chatHistory.Add(assistantMsg1);

        var assistantMsg2 = new ChatMessageContent(AuthorRole.Assistant, (string?)null);
        assistantMsg2.Items.Add(new FunctionCallContent(
            functionName: "GetTeamsDistributionList",
            pluginName: "DistributionList",
            id: "tooluse_sMmlRWbbCGd0lnhiLjvk8H",
            arguments: new KernelArguments { { "distributionListName", "developers" } }));
        chatHistory.Add(assistantMsg2);

        // Two separate tool result messages
        var toolResult1 = new ChatMessageContent(AuthorRole.Tool, (string?)null);
        toolResult1.Items.Add(new FunctionResultContent(
            functionName: "GetFeeds",
            pluginName: "Feeds",
            callId: "tooluse_G64hibpFmRqXEcAYwOfP5s",
            result: "Dataset DataReference: memory://8df2be02a23c4ebfb77e1170dea6c4b4. Dataset size: 78 items."));
        chatHistory.Add(toolResult1);

        var toolResult2 = new ChatMessageContent(AuthorRole.Tool, (string?)null);
        toolResult2.Items.Add(new FunctionResultContent(
            functionName: "GetTeamsDistributionList",
            pluginName: "DistributionList",
            callId: "tooluse_sMmlRWbbCGd0lnhiLjvk8H",
            result: "19:791df3464b4f4c3fac8429041e8e2540@thread.v2"));
        chatHistory.Add(toolResult2);

        // Act
        var messages = Core.BedrockModelUtilities.BuildMessageList(chatHistory);

        // Assert: Should produce exactly 3 messages: user, assistant (merged), user/tool-results (merged)
        Assert.Equal(3, messages.Count);

        // Message 1: User prompt
        Assert.Equal(ConversationRole.User, messages[0].Role);
        Assert.Single(messages[0].Content);
        Assert.Equal("Audit the feeds and get the developers distribution list", messages[0].Content[0].Text);

        // Message 2: Merged assistant with both tool use blocks
        Assert.Equal(ConversationRole.Assistant, messages[1].Role);
        Assert.Equal(2, messages[1].Content.Count);
        Assert.NotNull(messages[1].Content[0].ToolUse);
        Assert.NotNull(messages[1].Content[1].ToolUse);

        // Verify tool use IDs are preserved correctly
        var toolUseIds = messages[1].Content.Select(c => c.ToolUse.ToolUseId).ToList();
        Assert.Contains("tooluse_G64hibpFmRqXEcAYwOfP5s", toolUseIds);
        Assert.Contains("tooluse_sMmlRWbbCGd0lnhiLjvk8H", toolUseIds);

        // Message 3: Merged tool results (as user role)
        Assert.Equal(ConversationRole.User, messages[2].Role);
        Assert.Equal(2, messages[2].Content.Count);
        Assert.NotNull(messages[2].Content[0].ToolResult);
        Assert.NotNull(messages[2].Content[1].ToolResult);

        // Verify tool result IDs match the tool use IDs
        var toolResultIds = messages[2].Content.Select(c => c.ToolResult.ToolUseId).ToList();
        Assert.Contains("tooluse_G64hibpFmRqXEcAYwOfP5s", toolResultIds);
        Assert.Contains("tooluse_sMmlRWbbCGd0lnhiLjvk8H", toolResultIds);
    }

    /// <summary>
    /// Verifies that Tool role maps to User in the Bedrock conversation role.
    /// </summary>
    [Fact]
    public void MapAuthorRoleToConversationRoleShouldMapToolToUser()
    {
        // Act
        var result = Core.BedrockModelUtilities.MapAuthorRoleToConversationRole(AuthorRole.Tool);

        // Assert
        Assert.Equal(ConversationRole.User, result);
    }

    /// <summary>
    /// Verifies that FunctionCallContent without a plugin name uses just the function name.
    /// </summary>
    [Fact]
    public void BuildMessageListShouldUseOnlyFunctionNameWhenNoPluginName()
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Do something");

        var assistantMessage = new ChatMessageContent(AuthorRole.Assistant, (string?)null);
        assistantMessage.Items.Add(new FunctionCallContent(
            functionName: "MyFunction",
            id: "tool_123"));
        chatHistory.Add(assistantMessage);

        // Act
        var messages = Core.BedrockModelUtilities.BuildMessageList(chatHistory);

        // Assert
        Assert.Equal(2, messages.Count);
        Assert.NotNull(messages[1].Content[0].ToolUse);
        Assert.Equal("MyFunction", messages[1].Content[0].ToolUse.Name);
    }

    /// <summary>
    /// Verifies that tool call arguments are properly converted to Document.
    /// </summary>
    [Fact]
    public void BuildMessageListShouldConvertFunctionCallArguments()
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Search for something");

        var assistantMessage = new ChatMessageContent(AuthorRole.Assistant, (string?)null);
        assistantMessage.Items.Add(new FunctionCallContent(
            functionName: "Search",
            pluginName: "Web",
            id: "tool_456",
            arguments: new KernelArguments
            {
                { "query", "semantic kernel" },
                { "maxResults", 10 }
            }));
        chatHistory.Add(assistantMessage);

        // Act
        var messages = Core.BedrockModelUtilities.BuildMessageList(chatHistory);

        // Assert
        var toolUse = messages[1].Content[0].ToolUse;
        Assert.NotNull(toolUse);
        Assert.Equal("Web-Search", toolUse.Name);
        Assert.True(toolUse.Input.IsDictionary());
        var inputDict = toolUse.Input.AsDictionary();
        Assert.Equal("semantic kernel", inputDict["query"].AsString());
        Assert.Equal(10, inputDict["maxResults"].AsInt());
    }

    /// <summary>
    /// Verifies that non-consecutive same-role messages are NOT merged.
    /// </summary>
    [Fact]
    public void BuildMessageListShouldNotMergeNonConsecutiveSameRoleMessages()
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");
        chatHistory.AddAssistantMessage("Hi");
        chatHistory.AddUserMessage("How are you?");

        // Act
        var messages = Core.BedrockModelUtilities.BuildMessageList(chatHistory);

        // Assert: All three messages should be separate
        Assert.Equal(3, messages.Count);
    }

    /// <summary>
    /// Verifies that mixed text and tool content in a single assistant message works.
    /// </summary>
    [Fact]
    public void BuildMessageListShouldHandleAssistantMessageWithTextAndToolCall()
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What's the weather?");

        var assistantMessage = new ChatMessageContent(AuthorRole.Assistant, (string?)null);
        assistantMessage.Items.Add(new TextContent("Let me check the weather for you."));
        assistantMessage.Items.Add(new FunctionCallContent(
            functionName: "GetWeather",
            pluginName: "Weather",
            id: "tool_789",
            arguments: new KernelArguments { { "city", "Seattle" } }));
        chatHistory.Add(assistantMessage);

        // Act
        var messages = Core.BedrockModelUtilities.BuildMessageList(chatHistory);

        // Assert
        Assert.Equal(2, messages.Count);
        var assistantMsg = messages[1];
        Assert.Equal(2, assistantMsg.Content.Count);
        Assert.Equal("Let me check the weather for you.", assistantMsg.Content[0].Text);
        Assert.NotNull(assistantMsg.Content[1].ToolUse);
        Assert.Equal("Weather-GetWeather", assistantMsg.Content[1].ToolUse.Name);
    }
}

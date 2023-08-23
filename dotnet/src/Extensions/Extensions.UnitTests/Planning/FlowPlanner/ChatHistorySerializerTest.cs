// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Extensions.UnitTests.Planning.FlowPlanner;

using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Planning.Flow;
using Xunit;

public class ChatHistorySerializerTest
{
    [Fact]
    public void CanDeserializeChatHistory()
    {
        string input = "[{\"Role\":\"assistant\",\"Content\":\"To configure the email notification, please provide the following information:\\n\\n1. Email address: (Enter the valid email address)\\n2. Notification time: (Enter the schedule of notification)\\n3. Email Content: (Enter the content expected from email notification)\\n\\nOnce you have provided this information, please type \\u0022confirmed\\u0022 to confirm the details.\"}]\r\n";
        var history = ChatHistorySerializer.Deserialize(input);

        Assert.NotNull(history);
        Assert.Single(history);
        Assert.Equal(AuthorRole.Assistant.Label, history[0].Role.Label);
    }

    [Fact]
    public void CanSerializeChatHistory()
    {
        var history = new ChatHistory();
        var systemMessage = "system";
        var userMessage = "user";
        var assistantMessage = "assistant";

        history.AddSystemMessage(systemMessage);
        history.AddUserMessage(userMessage);
        history.AddAssistantMessage(assistantMessage);

        var serialized = ChatHistorySerializer.Serialize(history);
        var deserialized = ChatHistorySerializer.Deserialize(serialized);

        Assert.NotNull(deserialized);

        Assert.Equal(deserialized[0].Role, AuthorRole.System);
        Assert.Equal(deserialized[0].Content, systemMessage);

        Assert.Equal(deserialized[1].Role, AuthorRole.User);
        Assert.Equal(deserialized[1].Content, userMessage);

        Assert.Equal(deserialized[2].Role, AuthorRole.Assistant);
        Assert.Equal(deserialized[2].Content, assistantMessage);
    }
}

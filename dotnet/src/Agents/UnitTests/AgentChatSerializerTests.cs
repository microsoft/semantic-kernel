// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests;

/// <summary>
/// Unit testing of <see cref="AgentChat"/>.
/// </summary>
public class AgentChatSerializerTests
{
    /// <summary>
    /// Verify serialization cycle for an empty <see cref="AgentChat"/>.
    /// </summary>
    [Fact]
    public async Task VerifySerializedChatEmptyAsync()
    {
        // Create chat
        TestChat chat = new();

        // Serialize and deserialize chat
        AgentChatState chatState = chat.Serialize();
        string jsonState = await this.SerializeChatAsync(chat);
        AgentChatState? restoredState = JsonSerializer.Deserialize<AgentChatState>(jsonState);

        // Validate state
        Assert.Empty(chatState.Participants);
        ChatHistory? chatHistory = JsonSerializer.Deserialize<ChatHistory>(chatState.History);
        Assert.NotNull(chatHistory);
        Assert.Empty(chatHistory);
        Assert.Empty(chatState.Channels);

        Assert.NotNull(restoredState);
        Assert.Empty(restoredState.Participants);
        ChatHistory? restoredHistory = JsonSerializer.Deserialize<ChatHistory>(restoredState.History);
        Assert.NotNull(restoredHistory);
        Assert.Empty(restoredHistory);
        Assert.Empty(restoredState.Channels);
    }

    /// <summary>
    /// Verify serialization cycle for a <see cref="AgentChat"/> with only user message (no channels).
    /// </summary>
    [Fact]
    public async Task VerifySerializedChatWithoutAgentsAsync()
    {
        // Create chat
        TestChat chat = new();
        chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, "test"));

        // Serialize and deserialize chat
        AgentChatState chatState = chat.Serialize();
        string jsonState = await this.SerializeChatAsync(chat);
        AgentChatState? restoredState = JsonSerializer.Deserialize<AgentChatState>(jsonState);

        // Validate state
        Assert.Empty(chatState.Participants);
        ChatHistory? chatHistory = JsonSerializer.Deserialize<ChatHistory>(chatState.History);
        Assert.NotNull(chatHistory);
        Assert.Single(chatHistory);
        Assert.Empty(chatState.Channels);

        Assert.NotNull(restoredState);
        Assert.Empty(restoredState.Participants);
        ChatHistory? restoredHistory = JsonSerializer.Deserialize<ChatHistory>(restoredState.History);
        Assert.NotNull(restoredHistory);
        Assert.Single(restoredHistory);
        Assert.Empty(restoredState.Channels);
    }

    /// <summary>
    /// Verify serialization cycle for a <see cref="AgentChat"/> with only user message (no channels).
    /// </summary>
    [Fact]
    public async Task VerifySerializedChatWithAgentsAsync()
    {
        // Create chat
        TestChat chat = new(new TestAgent());
        chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, "test"));
        ChatMessageContent[] messages = await chat.InvokeAsync().ToArrayAsync();

        // Serialize and deserialize chat
        AgentChatState chatState = chat.Serialize();
        string jsonState = await this.SerializeChatAsync(chat);
        AgentChatState? restoredState = JsonSerializer.Deserialize<AgentChatState>(jsonState);

        // Validate state
        Assert.Single(chatState.Participants);
        ChatHistory? chatHistory = JsonSerializer.Deserialize<ChatHistory>(chatState.History);
        Assert.NotNull(chatHistory);
        Assert.Equal(2, chatHistory.Count);
        Assert.Single(chatState.Channels);

        Assert.NotNull(restoredState);
        Assert.Single(restoredState.Participants);
        ChatHistory? restoredHistory = JsonSerializer.Deserialize<ChatHistory>(restoredState.History);
        Assert.NotNull(restoredHistory);
        Assert.Equal(2, restoredHistory.Count);
        Assert.Single(restoredState.Channels);
    }

    /// <summary>
    /// Verify serialization cycle for a <see cref="AgentChat"/> with only user message (no channels).
    /// </summary>
    [Fact]
    public async Task VerifyDeserializedChatWithAgentsAsync()
    {
        // Create chat
        TestChat chat = new(new TestAgent());
        chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, "test"));
        ChatMessageContent[] messages = await chat.InvokeAsync().ToArrayAsync();

        // Serialize and deserialize chat
        AgentChatSerializer serializer = await this.CreateSerializerAsync(chat);

        TestChat copy = new(new TestAgent());

        await serializer.DeserializeAsync(copy);

        // Validate chat state
        ChatMessageContent[] history = await copy.GetChatMessagesAsync().ToArrayAsync();
        Assert.Equal(2, history.Length);

        await copy.InvokeAsync().ToArrayAsync();
        history = await copy.GetChatMessagesAsync().ToArrayAsync();
        Assert.Equal(3, history.Length);
    }

    /// <summary>
    /// Verify serialization cycle for a <see cref="AgentChat"/> with only user message (no channels).
    /// </summary>
    [Fact]
    public async Task VerifyDeserializedChatWithActivityAsync()
    {
        // Create chat
        TestChat chat = new(new TestAgent());

        // Serialize and deserialize chat
        AgentChatSerializer serializer = await this.CreateSerializerAsync(chat);

        TestChat copy = new(new TestAgent());
        ChatMessageContent[] messages = await copy.InvokeAsync().ToArrayAsync();

        // Verify exception
        await Assert.ThrowsAsync<KernelException>(() => serializer.DeserializeAsync(copy));
    }

    /// <summary>
    /// Verify serialization cycle for a <see cref="AgentChat"/> with only user message (no channels).
    /// </summary>
    [Fact]
    public async Task VerifyDeserializedChatWithUserMessageAsync()
    {
        // Create chat
        TestChat chat = new(new TestAgent());

        // Serialize and deserialize chat
        AgentChatSerializer serializer = await this.CreateSerializerAsync(chat);

        TestChat copy = new(new TestAgent());
        copy.AddChatMessage(new ChatMessageContent(AuthorRole.User, "test"));

        // Verify exception
        await Assert.ThrowsAsync<KernelException>(() => serializer.DeserializeAsync(copy));
    }

    private async Task<AgentChatSerializer> CreateSerializerAsync(TestChat chat)
    {
        string jsonState = await this.SerializeChatAsync(chat);
        await using MemoryStream stream = new();
        await using StreamWriter writer = new(stream);
        writer.Write(jsonState);
        writer.Flush();
        stream.Position = 0;

        return await AgentChatSerializer.DeserializeAsync(stream);
    }

    private async Task<string> SerializeChatAsync(TestChat chat)
    {
        await using MemoryStream stream = new();
        await AgentChatSerializer.SerializeAsync(chat, stream);

        stream.Position = 0;
        using StreamReader reader = new(stream);
        return reader.ReadToEnd();
    }

    private sealed class TestChat(params Agent[] agents) : AgentChat
    {
        public override IReadOnlyList<Agent> Agents => agents;

        public override IAsyncEnumerable<ChatMessageContent> InvokeAsync(
            CancellationToken cancellationToken = default) =>
                this.InvokeAgentAsync(this.Agents[0], cancellationToken);
    }

    private sealed class TestAgent : ChatHistoryKernelAgent
    {
        public int InvokeCount { get; private set; }

        public override IAsyncEnumerable<ChatMessageContent> InvokeAsync(
            ChatHistory history,
            CancellationToken cancellationToken = default)
        {
            this.InvokeCount++;

            return new ChatMessageContent[] { new(AuthorRole.Assistant, "sup") }.ToAsyncEnumerable();
        }

        public override IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
            ChatHistory history,
            CancellationToken cancellationToken = default)
        {
            this.InvokeCount++;

            StreamingChatMessageContent[] contents = [new(AuthorRole.Assistant, "sup")];

            return contents.ToAsyncEnumerable();
        }
    }
}

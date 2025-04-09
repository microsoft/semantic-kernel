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
    /// Verify serialization cycle for a <see cref="AgentChat"/> with history and channels.
    /// </summary>
    [Fact]
    public async Task VerifySerializedChatWithAgentsAsync()
    {
        // Create chat
        TestChat chat = new(CreateMockAgent(), CreateMockAgent());
        chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, "test"));
        ChatMessageContent[] messages = await chat.InvokeAsync().ToArrayAsync();

        // Serialize and deserialize chat
        AgentChatState chatState = chat.Serialize();
        string jsonState = await this.SerializeChatAsync(chat);
        AgentChatState? restoredState = JsonSerializer.Deserialize<AgentChatState>(jsonState);

        // Validate state
        Assert.Equal(2, chatState.Participants.Count());
        ChatHistory? chatHistory = JsonSerializer.Deserialize<ChatHistory>(chatState.History);
        Assert.NotNull(chatHistory);
        Assert.Equal(2, chatHistory.Count);
        Assert.Single(chatState.Channels);

        Assert.NotNull(restoredState);
        Assert.Equal(2, restoredState.Participants.Count());
        ChatHistory? restoredHistory = JsonSerializer.Deserialize<ChatHistory>(restoredState.History);
        Assert.NotNull(restoredHistory);
        Assert.Equal(2, restoredHistory.Count);
        Assert.Single(restoredState.Channels);
    }

    /// <summary>
    /// Verify serialization cycle for a <see cref="AgentChat"/> with a <see cref="AggregatorAgent"/>.
    /// </summary>
    [Fact]
    public async Task VerifySerializedChatWithAggregatorAsync()
    {
        // Create chat
        TestChat chat = new(new AggregatorAgent(() => new TestChat(CreateMockAgent())));
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
    /// Verify Deserialization cycle for a <see cref="AgentChat"/> with history and channels.
    /// </summary>
    [Fact]
    public async Task VerifyDeserializedChatWithAgentsAsync()
    {
        // Create chat
        TestChat chat = new(CreateMockAgent(), CreateMockAgent());
        chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, "test"));
        ChatMessageContent[] messages = await chat.InvokeAsync().ToArrayAsync();

        // Serialize and deserialize chat
        AgentChatSerializer serializer = await this.CreateSerializerAsync(chat);
        Assert.Equal(2, serializer.Participants.Count());

        TestChat copy = new(CreateMockAgent(), CreateMockAgent());

        await serializer.DeserializeAsync(copy);

        // Validate chat state
        ChatMessageContent[] history = await copy.GetChatMessagesAsync().ToArrayAsync();
        Assert.Equal(2, history.Length);

        await copy.InvokeAsync().ToArrayAsync();
        history = await copy.GetChatMessagesAsync().ToArrayAsync();
        Assert.Equal(3, history.Length);
    }

    /// <summary>
    /// Verify deserialization cycle for a <see cref="AgentChat"/> with <see cref="AggregatorAgent"/>.
    /// </summary>
    [Fact]
    public async Task VerifyDeserializedChatWithAggregatorAsync()
    {
        // Create chat
        TestChat chat = new(new AggregatorAgent(() => new TestChat(CreateMockAgent())) { Name = "Group" });
        chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, "test"));
        ChatMessageContent[] messages = await chat.InvokeAsync().ToArrayAsync();

        // Serialize and deserialize chat
        AgentChatSerializer serializer = await this.CreateSerializerAsync(chat);
        Assert.Single(serializer.Participants);

        TestChat copy = new(new AggregatorAgent(() => new TestChat(CreateMockAgent())) { Name = "Group" });

        await serializer.DeserializeAsync(copy);

        // Validate chat state
        ChatMessageContent[] history = await copy.GetChatMessagesAsync().ToArrayAsync();
        Assert.Equal(2, history.Length);

        await copy.InvokeAsync().ToArrayAsync();
        history = await copy.GetChatMessagesAsync().ToArrayAsync();
        Assert.Equal(3, history.Length);
    }

    /// <summary>
    /// Verify deserialization into a <see cref="AgentChat"/> that already has history and channels.
    /// </summary>
    [Fact]
    public async Task VerifyDeserializedChatWithActivityAsync()
    {
        // Create chat
        TestChat chat = new(CreateMockAgent());

        // Serialize and deserialize chat
        AgentChatSerializer serializer = await this.CreateSerializerAsync(chat);

        TestChat copy = new(CreateMockAgent());
        ChatMessageContent[] messages = await copy.InvokeAsync().ToArrayAsync();

        // Verify exception
        await Assert.ThrowsAsync<KernelException>(() => serializer.DeserializeAsync(copy));
    }

    /// <summary>
    /// Verify deserialization into a <see cref="AgentChat"/> with only user message (no channels).
    /// </summary>
    [Fact]
    public async Task VerifyDeserializedChatWithUserMessageAsync()
    {
        // Create chat
        TestChat chat = new(CreateMockAgent());

        // Serialize and deserialize chat
        AgentChatSerializer serializer = await this.CreateSerializerAsync(chat);

        TestChat copy = new(CreateMockAgent());
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

    private static MockAgent CreateMockAgent() => new() { Response = [new(AuthorRole.Assistant, "sup")] };

    private sealed class TestChat(params Agent[] agents) : AgentChat
    {
        public override IReadOnlyList<Agent> Agents => agents;

        public override IAsyncEnumerable<ChatMessageContent> InvokeAsync(
            CancellationToken cancellationToken = default) =>
                this.InvokeAgentAsync(this.Agents[0], cancellationToken);

        public override IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(CancellationToken cancellationToken = default)
        {
            throw new System.NotImplementedException();
        }
    }
}

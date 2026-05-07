// Copyright (c) Microsoft. All rights reserved.
using System;
using System.ClientModel;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using OpenAI.Assistants;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Unit testing of <see cref="OpenAIAssistantAgent"/>.
/// </summary>
#pragma warning disable CS0419 // Ambiguous reference in cref attribute
public sealed class OpenAIAssistantAgentTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;
    private readonly Kernel _emptyKernel;

    /// <summary>
    /// Verify invocation via <see cref="AgentGroupChat"/>.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentGroupChatAsync()
    {
        // Arrange
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();

        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.CreateThread,
            OpenAIAssistantResponseContent.Run.CreateRun,
            OpenAIAssistantResponseContent.Run.CompletedRun,
            OpenAIAssistantResponseContent.Run.MessageSteps,
            OpenAIAssistantResponseContent.GetTextMessage());

        AgentGroupChat chat = new();

        // Act
        ChatMessageContent[] messages = await chat.InvokeAsync(agent).ToArrayAsync();

        // Assert
        Assert.Single(messages);
        Assert.Single(messages[0].Items);
        Assert.IsType<Microsoft.SemanticKernel.TextContent>(messages[0].Items[0]);

        // Arrange
        this.SetupResponse(HttpStatusCode.OK, OpenAIAssistantResponseContent.DeleteThread);

        // Act
        await chat.ResetAsync();

        // Assert
        Assert.Empty(this._messageHandlerStub.ResponseQueue);
    }

    /// <summary>
    /// Verify direct invocation of <see cref="OpenAIAssistantAgent"/> using <see cref="AgentThread"/>.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentInvokeWithThreadAsync()
    {
        // Arrange
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();

        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.CreateThread,
            // Create message response
            OpenAIAssistantResponseContent.GetTextMessage("Hi"),
            OpenAIAssistantResponseContent.Run.CreateRun,
            OpenAIAssistantResponseContent.Run.CompletedRun,
            OpenAIAssistantResponseContent.Run.MessageSteps,
            OpenAIAssistantResponseContent.GetTextMessage("Hello, how can I help you?"));

        // Act
        AgentResponseItem<ChatMessageContent>[] messages = await agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, "Hi")).ToArrayAsync();

        // Assert
        Assert.Single(messages);
        Assert.Single(messages[0].Message.Items);
        Assert.IsType<Microsoft.SemanticKernel.TextContent>(messages[0].Message.Items[0]);
        Assert.Equal("Hello, how can I help you?", messages[0].Message.Content);
    }

    /// <summary>
    /// Verify direct invocation of <see cref="OpenAIAssistantAgent"/> using <see cref="AgentThread"/>.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentInvokeMultipleMessagesWithThreadAsync()
    {
        // Arrange
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();

        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.CreateThread,
            // Create message response
            OpenAIAssistantResponseContent.GetTextMessage("Hello"),
            // Create message response
            OpenAIAssistantResponseContent.GetTextMessage("Hi"),
            OpenAIAssistantResponseContent.Run.CreateRun,
            OpenAIAssistantResponseContent.Run.CompletedRun,
            OpenAIAssistantResponseContent.Run.MessageSteps,
            OpenAIAssistantResponseContent.GetTextMessage("How can I help you?"));

        // Act
        AgentResponseItem<ChatMessageContent>[] messages = await agent.InvokeAsync(
        [
            new ChatMessageContent(AuthorRole.Assistant, "Hello"),
            new ChatMessageContent(AuthorRole.User, "Hi")
        ]).ToArrayAsync();

        // Assert
        Assert.Single(messages);
        Assert.Single(messages[0].Message.Items);
        Assert.IsType<Microsoft.SemanticKernel.TextContent>(messages[0].Message.Items[0]);
        Assert.Equal("How can I help you?", messages[0].Message.Content);
    }

    /// <summary>
    /// Verify direct streaming invocation of <see cref="OpenAIAssistantAgent"/> using <see cref="AgentThread"/>.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentInvokeStreamingWithThreadAsync()
    {
        // Arrange
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();

        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.CreateThread,
            // Create message response
            OpenAIAssistantResponseContent.GetTextMessage("Hi"),
            OpenAIAssistantResponseContent.Streaming.Response(
            [
                OpenAIAssistantResponseContent.Streaming.CreateRun("created"),
                OpenAIAssistantResponseContent.Streaming.CreateRun("queued"),
                OpenAIAssistantResponseContent.Streaming.CreateRun("in_progress"),
                OpenAIAssistantResponseContent.Streaming.DeltaMessage("Hello, "),
                OpenAIAssistantResponseContent.Streaming.DeltaMessage("how can I "),
                OpenAIAssistantResponseContent.Streaming.DeltaMessage("help you?"),
                OpenAIAssistantResponseContent.Streaming.CreateRun("completed"),
                OpenAIAssistantResponseContent.Streaming.Done
            ]),
            OpenAIAssistantResponseContent.GetTextMessage("Hello, how can I help you?"));

        // Act
        Task OnIntermediateMessage(ChatMessageContent message)
        {
            // Assert intermediate messages
            Assert.NotNull(message);
            Assert.Equal("Hello, how can I help you?", message.Content);
            return Task.CompletedTask;
        }
        AgentResponseItem<StreamingChatMessageContent>[] messages = await agent.InvokeStreamingAsync(new ChatMessageContent(AuthorRole.User, "Hi"), options: new() { OnIntermediateMessage = OnIntermediateMessage }).ToArrayAsync();

        // Assert
        Assert.Equal(3, messages.Length);
        var combinedMessage = string.Concat(messages.Select(x => x.Message.Content));
        Assert.Equal("Hello, how can I help you?", combinedMessage);
    }

    /// <summary>
    /// Verify complex chat interaction across multiple states.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentChatTextMessageWithAnnotationAsync()
    {
        // Arrange
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();

        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.CreateThread,
            OpenAIAssistantResponseContent.Run.CreateRun,
            OpenAIAssistantResponseContent.Run.CompletedRun,
            OpenAIAssistantResponseContent.Run.MessageSteps,
            OpenAIAssistantResponseContent.GetTextMessageWithAnnotation);

        AgentGroupChat chat = new();

        // Act
        ChatMessageContent[] messages = await chat.InvokeAsync(agent).ToArrayAsync();

        // Assert
        Assert.Single(messages);
        Assert.Equal(2, messages[0].Items.Count);
        Assert.NotNull(messages[0].Items.SingleOrDefault(c => c is Microsoft.SemanticKernel.TextContent));
        Assert.NotNull(messages[0].Items.SingleOrDefault(c => c is AnnotationContent));
    }

    /// <summary>
    /// Verify complex chat interaction across multiple states.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentChatImageMessageAsync()
    {
        // Arrange
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();

        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.CreateThread,
            OpenAIAssistantResponseContent.Run.CreateRun,
            OpenAIAssistantResponseContent.Run.CompletedRun,
            OpenAIAssistantResponseContent.Run.MessageSteps,
            OpenAIAssistantResponseContent.GetImageMessage);

        AgentGroupChat chat = new();

        // Act
        ChatMessageContent[] messages = await chat.InvokeAsync(agent).ToArrayAsync();

        // Assert
        Assert.Single(messages);
        Assert.Single(messages[0].Items);
        Assert.IsType<FileReferenceContent>(messages[0].Items[0]);
    }

    /// <summary>
    /// Verify complex chat interaction across multiple states.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentGetMessagesAsync()
    {
        // Arrange: Create agent
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();

        // Initialize agent channel
        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.CreateThread,
            OpenAIAssistantResponseContent.Run.CreateRun,
            OpenAIAssistantResponseContent.Run.CompletedRun,
            OpenAIAssistantResponseContent.Run.MessageSteps,
            OpenAIAssistantResponseContent.GetTextMessage());

        AgentGroupChat chat = new();

        // Act
        ChatMessageContent[] messages = await chat.InvokeAsync(agent).ToArrayAsync();
        // Assert
        Assert.Single(messages);

        // Arrange: Setup messages
        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.ListMessagesPageMore,
            OpenAIAssistantResponseContent.ListMessagesPageMore,
            OpenAIAssistantResponseContent.ListMessagesPageFinal);

        // Act: Get messages
        messages = await chat.GetChatMessagesAsync(agent).ToArrayAsync();
        // Assert
        Assert.Equal(5, messages.Length);
    }

    /// <summary>
    /// Verify complex chat interaction across multiple states.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentAddMessagesAsync()
    {
        // Arrange: Create agent
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();

        // Initialize agent channel
        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.CreateThread,
            OpenAIAssistantResponseContent.Run.CreateRun,
            OpenAIAssistantResponseContent.Run.CompletedRun,
            OpenAIAssistantResponseContent.Run.MessageSteps,
            OpenAIAssistantResponseContent.GetTextMessage());
        AgentGroupChat chat = new();

        // Act
        ChatMessageContent[] messages = await chat.InvokeAsync(agent).ToArrayAsync();
        // Assert
        Assert.Single(messages);

        // Arrange
        chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, "hi"));

        // Act
        messages = await chat.GetChatMessagesAsync().ToArrayAsync();
        // Assert
        Assert.Equal(2, messages.Length);
    }

    /// <summary>
    /// Verify ability to list agent definitions.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentWithFunctionCallAsync()
    {
        // Arrange
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MyPlugin>();
        agent.Kernel.Plugins.Add(plugin);

        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.CreateThread,
            OpenAIAssistantResponseContent.Run.CreateRun,
            OpenAIAssistantResponseContent.Run.PendingRun,
            OpenAIAssistantResponseContent.Run.ToolSteps,
            OpenAIAssistantResponseContent.ToolResponse,
            OpenAIAssistantResponseContent.Run.CompletedRun,
            OpenAIAssistantResponseContent.Run.MessageSteps,
            OpenAIAssistantResponseContent.GetTextMessage());

        AgentGroupChat chat = new();

        // Act
        ChatMessageContent[] messages = await chat.InvokeAsync(agent).ToArrayAsync();

        // Assert
        Assert.Single(messages);
        Assert.Single(messages[0].Items);
        Assert.IsType<Microsoft.SemanticKernel.TextContent>(messages[0].Items[0]);
    }

    /// <summary>
    /// Verify that InvalidOperationException is thrown when UseImmutableKernel is false and AIFunctions exist.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentThrowsWhenUseImmutableKernelFalseWithAIFunctionsAsync()
    {
        // Arrange
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();
        agent.UseImmutableKernel = false; // Explicitly set to false

        // Initialize agent channel
        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.CreateThread,
            OpenAIAssistantResponseContent.Run.CreateRun,
            OpenAIAssistantResponseContent.Run.CompletedRun,
            OpenAIAssistantResponseContent.Run.MessageSteps,
            OpenAIAssistantResponseContent.GetTextMessage());

        var mockAIContextProvider = new Mock<AIContextProvider>();
        var aiContext = new AIContext
        {
            AIFunctions = [new TestAIFunction("TestFunction", "Test function description")]
        };
        mockAIContextProvider.Setup(p => p.ModelInvokingAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
                           .ReturnsAsync(aiContext);

        var thread = new OpenAIAssistantAgentThread(agent.Client);
        thread.AIContextProviders.Add(mockAIContextProvider.Object);

        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.CreateThread);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(
            async () => await agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, "Hi"), thread: thread).ToArrayAsync());

        Assert.NotNull(exception);
    }

    /// <summary>
    /// Verify that InvalidOperationException is thrown when UseImmutableKernel is default (false) and AIFunctions exist.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentThrowsWhenUseImmutableKernelDefaultWithAIFunctionsAsync()
    {
        // Arrange
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();
        // UseImmutableKernel not set, should default to false

        // Initialize agent channel
        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.CreateThread,
            OpenAIAssistantResponseContent.Run.CreateRun,
            OpenAIAssistantResponseContent.Run.CompletedRun,
            OpenAIAssistantResponseContent.Run.MessageSteps,
            OpenAIAssistantResponseContent.GetTextMessage());

        var mockAIContextProvider = new Mock<AIContextProvider>();
        var aiContext = new AIContext
        {
            AIFunctions = [new TestAIFunction("TestFunction", "Test function description")]
        };
        mockAIContextProvider.Setup(p => p.ModelInvokingAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
                           .ReturnsAsync(aiContext);

        var thread = new OpenAIAssistantAgentThread(agent.Client);
        thread.AIContextProviders.Add(mockAIContextProvider.Object);

        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.CreateThread);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(
            async () => await agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, "Hi"), thread: thread).ToArrayAsync());

        Assert.NotNull(exception);
    }

    /// <summary>
    /// Verify that kernel remains immutable when UseImmutableKernel is true.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentKernelImmutabilityWhenUseImmutableKernelTrueAsync()
    {
        // Arrange
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();
        agent.UseImmutableKernel = true;

        var originalKernel = agent.Kernel;
        var originalPluginCount = originalKernel.Plugins.Count;

        var mockAIContextProvider = new Mock<AIContextProvider>();
        var aiContext = new AIContext
        {
            AIFunctions = [new TestAIFunction("TestFunction", "Test function description")]
        };
        mockAIContextProvider.Setup(p => p.ModelInvokingAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
                           .ReturnsAsync(aiContext);

        var thread = new OpenAIAssistantAgentThread(agent.Client);
        thread.AIContextProviders.Add(mockAIContextProvider.Object);

        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.CreateThread,
            // Create message response
            OpenAIAssistantResponseContent.GetTextMessage("Hi"),
            OpenAIAssistantResponseContent.Run.CreateRun,
            OpenAIAssistantResponseContent.Run.CompletedRun,
            OpenAIAssistantResponseContent.Run.MessageSteps,
            OpenAIAssistantResponseContent.GetTextMessage("Hello, how can I help you?"));

        // Act
        AgentResponseItem<ChatMessageContent>[] result = await agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, "Hi"), thread: thread).ToArrayAsync();

        // Assert
        Assert.Single(result);

        // Verify original kernel was not modified
        Assert.Equal(originalPluginCount, originalKernel.Plugins.Count);

        // The kernel should remain unchanged since UseImmutableKernel=true creates a clone
        Assert.Same(originalKernel, agent.Kernel);
    }

    /// <summary>
    /// Verify that mutable kernel behavior works when UseImmutableKernel is false and no AIFunctions exist.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentMutableKernelWhenUseImmutableKernelFalseNoAIFunctionsAsync()
    {
        // Arrange
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();
        agent.UseImmutableKernel = false;

        var originalKernel = agent.Kernel;
        var originalPluginCount = originalKernel.Plugins.Count;

        var mockAIContextProvider = new Mock<AIContextProvider>();
        var aiContext = new AIContext
        {
            AIFunctions = [] // Empty AIFunctions list
        };
        mockAIContextProvider.Setup(p => p.ModelInvokingAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
                           .ReturnsAsync(aiContext);

        var thread = new OpenAIAssistantAgentThread(agent.Client);
        thread.AIContextProviders.Add(mockAIContextProvider.Object);

        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.CreateThread,
            // Create message response
            OpenAIAssistantResponseContent.GetTextMessage("Hi"),
            OpenAIAssistantResponseContent.Run.CreateRun,
            OpenAIAssistantResponseContent.Run.CompletedRun,
            OpenAIAssistantResponseContent.Run.MessageSteps,
            OpenAIAssistantResponseContent.GetTextMessage("Hello, how can I help you?"));

        // Act
        AgentResponseItem<ChatMessageContent>[] result = await agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, "Hi"), thread: thread).ToArrayAsync();

        // Assert
        Assert.Single(result);

        // Verify the same kernel instance is still being used (mutable behavior)
        Assert.Same(originalKernel, agent.Kernel);
    }

    /// <summary>
    /// Verify that InvalidOperationException is thrown when UseImmutableKernel is false and AIFunctions exist (streaming).
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentStreamingThrowsWhenUseImmutableKernelFalseWithAIFunctionsAsync()
    {
        // Arrange
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();
        agent.UseImmutableKernel = false; // Explicitly set to false

        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.CreateThread,
            // Create message response
            OpenAIAssistantResponseContent.GetTextMessage("Hi"),
            OpenAIAssistantResponseContent.Streaming.Response(
            [
                OpenAIAssistantResponseContent.Streaming.CreateRun("created"),
                        OpenAIAssistantResponseContent.Streaming.CreateRun("queued"),
                        OpenAIAssistantResponseContent.Streaming.CreateRun("in_progress"),
                        OpenAIAssistantResponseContent.Streaming.DeltaMessage("Hello, "),
                        OpenAIAssistantResponseContent.Streaming.DeltaMessage("how can I "),
                        OpenAIAssistantResponseContent.Streaming.DeltaMessage("help you?"),
                        OpenAIAssistantResponseContent.Streaming.CreateRun("completed"),
                        OpenAIAssistantResponseContent.Streaming.Done
            ]),
            OpenAIAssistantResponseContent.GetTextMessage("Hello, how can I help you?"));

        var mockAIContextProvider = new Mock<AIContextProvider>();
        var aiContext = new AIContext
        {
            AIFunctions = [new TestAIFunction("TestFunction", "Test function description")]
        };
        mockAIContextProvider.Setup(p => p.ModelInvokingAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
                           .ReturnsAsync(aiContext);

        var thread = new OpenAIAssistantAgentThread(agent.Client);
        thread.AIContextProviders.Add(mockAIContextProvider.Object);

        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.CreateThread);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(
            async () => await agent.InvokeStreamingAsync(new ChatMessageContent(AuthorRole.User, "Hi"), thread: thread).ToArrayAsync());

        Assert.NotNull(exception);
    }

    /// <summary>
    /// Verify that InvalidOperationException is thrown when UseImmutableKernel is default (false) and AIFunctions exist (streaming).
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentStreamingThrowsWhenUseImmutableKernelDefaultWithAIFunctionsAsync()
    {
        // Arrange
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();
        // UseImmutableKernel not set, should default to false

        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.CreateThread,
            // Create message response
            OpenAIAssistantResponseContent.GetTextMessage("Hi"),
            OpenAIAssistantResponseContent.Streaming.Response(
            [
                OpenAIAssistantResponseContent.Streaming.CreateRun("created"),
                        OpenAIAssistantResponseContent.Streaming.CreateRun("queued"),
                        OpenAIAssistantResponseContent.Streaming.CreateRun("in_progress"),
                        OpenAIAssistantResponseContent.Streaming.DeltaMessage("Hello, "),
                        OpenAIAssistantResponseContent.Streaming.DeltaMessage("how can I "),
                        OpenAIAssistantResponseContent.Streaming.DeltaMessage("help you?"),
                        OpenAIAssistantResponseContent.Streaming.CreateRun("completed"),
                        OpenAIAssistantResponseContent.Streaming.Done
            ]),
            OpenAIAssistantResponseContent.GetTextMessage("Hello, how can I help you?"));

        var mockAIContextProvider = new Mock<AIContextProvider>();
        var aiContext = new AIContext
        {
            AIFunctions = [new TestAIFunction("TestFunction", "Test function description")]
        };
        mockAIContextProvider.Setup(p => p.ModelInvokingAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
                           .ReturnsAsync(aiContext);

        var thread = new OpenAIAssistantAgentThread(agent.Client);
        thread.AIContextProviders.Add(mockAIContextProvider.Object);

        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.CreateThread);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(
            async () => await agent.InvokeStreamingAsync(new ChatMessageContent(AuthorRole.User, "Hi"), thread: thread).ToArrayAsync());

        Assert.NotNull(exception);
    }

    /// <summary>
    /// Verify that kernel remains immutable when UseImmutableKernel is true (streaming).
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentStreamingKernelImmutabilityWhenUseImmutableKernelTrueAsync()
    {
        // Arrange
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();
        agent.UseImmutableKernel = true;

        var originalKernel = agent.Kernel;
        var originalPluginCount = originalKernel.Plugins.Count;

        var mockAIContextProvider = new Mock<AIContextProvider>();
        var aiContext = new AIContext
        {
            AIFunctions = [new TestAIFunction("TestFunction", "Test function description")]
        };
        mockAIContextProvider.Setup(p => p.ModelInvokingAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
                           .ReturnsAsync(aiContext);

        var thread = new OpenAIAssistantAgentThread(agent.Client);
        thread.AIContextProviders.Add(mockAIContextProvider.Object);

        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.CreateThread,
            // Create message response
            OpenAIAssistantResponseContent.GetTextMessage("Hi"),
            OpenAIAssistantResponseContent.Streaming.Response(
            [
                OpenAIAssistantResponseContent.Streaming.CreateRun("created"),
                OpenAIAssistantResponseContent.Streaming.CreateRun("queued"),
                OpenAIAssistantResponseContent.Streaming.CreateRun("in_progress"),
                OpenAIAssistantResponseContent.Streaming.DeltaMessage("Hello, "),
                OpenAIAssistantResponseContent.Streaming.DeltaMessage("how can I "),
                OpenAIAssistantResponseContent.Streaming.DeltaMessage("help you?"),
                OpenAIAssistantResponseContent.Streaming.CreateRun("completed"),
                OpenAIAssistantResponseContent.Streaming.Done
            ]),
            OpenAIAssistantResponseContent.GetTextMessage("Hello, how can I help you?"));

        // Act
        AgentResponseItem<StreamingChatMessageContent>[] result = await agent.InvokeStreamingAsync(new ChatMessageContent(AuthorRole.User, "Hi"), thread: thread).ToArrayAsync();

        // Assert
        Assert.True(result.Length > 0);

        // Verify original kernel was not modified
        Assert.Equal(originalPluginCount, originalKernel.Plugins.Count);

        // The kernel should remain unchanged since UseImmutableKernel=true creates a clone
        Assert.Same(originalKernel, agent.Kernel);
    }

    /// <summary>
    /// Verify that mutable kernel behavior works when UseImmutableKernel is false and no AIFunctions exist (streaming).
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentStreamingMutableKernelWhenUseImmutableKernelFalseNoAIFunctionsAsync()
    {
        // Arrange
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();
        agent.UseImmutableKernel = false;

        var originalKernel = agent.Kernel;
        var originalPluginCount = originalKernel.Plugins.Count;

        var mockAIContextProvider = new Mock<AIContextProvider>();
        var aiContext = new AIContext
        {
            AIFunctions = [] // Empty AIFunctions list
        };
        mockAIContextProvider.Setup(p => p.ModelInvokingAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
                           .ReturnsAsync(aiContext);

        var thread = new OpenAIAssistantAgentThread(agent.Client);
        thread.AIContextProviders.Add(mockAIContextProvider.Object);

        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.CreateThread,
            // Create message response
            OpenAIAssistantResponseContent.GetTextMessage("Hi"),
            OpenAIAssistantResponseContent.Streaming.Response(
            [
                OpenAIAssistantResponseContent.Streaming.CreateRun("created"),
                OpenAIAssistantResponseContent.Streaming.CreateRun("queued"),
                OpenAIAssistantResponseContent.Streaming.CreateRun("in_progress"),
                OpenAIAssistantResponseContent.Streaming.DeltaMessage("Hello, "),
                OpenAIAssistantResponseContent.Streaming.DeltaMessage("how can I "),
                OpenAIAssistantResponseContent.Streaming.DeltaMessage("help you?"),
                OpenAIAssistantResponseContent.Streaming.CreateRun("completed"),
                OpenAIAssistantResponseContent.Streaming.Done
            ]),
            OpenAIAssistantResponseContent.GetTextMessage("Hello, how can I help you?"));

        // Act
        AgentResponseItem<StreamingChatMessageContent>[] result = await agent.InvokeStreamingAsync(new ChatMessageContent(AuthorRole.User, "Hi"), thread: thread).ToArrayAsync();

        // Assert
        Assert.True(result.Length > 0);

        // Verify the same kernel instance is still being used (mutable behavior)
        Assert.Same(originalKernel, agent.Kernel);
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this._messageHandlerStub.Dispose();
        this._httpClient.Dispose();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIAssistantAgentTests"/> class.
    /// </summary>
    public OpenAIAssistantAgentTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, disposeHandler: false);
        this._emptyKernel = new Kernel();
    }

    private static void ValidateAgentDefinition(OpenAIAssistantAgent agent, OpenAIAssistantDefinition expectedConfig)
    {
        ValidateAgent(agent, expectedConfig.Name, expectedConfig.Instructions, expectedConfig.Description, expectedConfig);
    }

    private static void ValidateAgentDefinition(OpenAIAssistantAgent agent, OpenAIAssistantCapabilities expectedConfig, PromptTemplateConfig templateConfig)
    {
        ValidateAgent(agent, templateConfig.Name, templateConfig.Template, templateConfig.Description, expectedConfig);
    }

    private static void ValidateAgent(
        OpenAIAssistantAgent agent,
        string? expectedName,
        string? expectedInstructions,
        string? expectedDescription,
        OpenAIAssistantCapabilities expectedConfig)
    {
        // Verify fundamental state
        Assert.NotNull(agent);
        Assert.NotNull(agent.Id);
        Assert.NotNull(agent.Definition);
        Assert.Equal(expectedConfig.ModelId, agent.Definition.Model);

        // Verify core properties
        Assert.Equal(expectedInstructions ?? string.Empty, agent.Instructions);
        Assert.Equal(expectedName ?? string.Empty, agent.Name);
        Assert.Equal(expectedDescription ?? string.Empty, agent.Description);

        // Verify options
        Assert.Equal(expectedConfig.Temperature, agent.Definition.Temperature);
        Assert.Equal(expectedConfig.TopP, agent.Definition.NucleusSamplingFactor);

        // Verify tool definitions
        int expectedToolCount = 0;

        bool hasCodeInterpreter = false;
        if (expectedConfig.EnableCodeInterpreter)
        {
            hasCodeInterpreter = true;
            ++expectedToolCount;
        }

        Assert.Equal(hasCodeInterpreter, agent.Definition.Tools.OfType<CodeInterpreterToolDefinition>().Any());

        bool hasFileSearch = false;
        if (expectedConfig.EnableFileSearch)
        {
            hasFileSearch = true;
            ++expectedToolCount;
        }

        Assert.Equal(hasFileSearch, agent.Definition.Tools.OfType<FileSearchToolDefinition>().Any());

        Assert.Equal(expectedToolCount, agent.Definition.Tools.Count);

        // Verify metadata
        Assert.NotNull(agent.Definition.Metadata);
        if (expectedConfig.ExecutionOptions == null)
        {
            Assert.Equal(expectedConfig.Metadata ?? new Dictionary<string, string>(), agent.Definition.Metadata);
        }
        else // Additional metadata present when execution options are defined
        {
            Assert.Equal((expectedConfig.Metadata?.Count ?? 0) + 1, agent.Definition.Metadata.Count);

            if (expectedConfig.Metadata != null)
            {
                foreach (var (key, value) in expectedConfig.Metadata)
                {
                    string? targetValue = agent.Definition.Metadata[key];
                    Assert.NotNull(targetValue);
                    Assert.Equal(value, targetValue);
                }
            }
        }

        // Verify detail definition
        Assert.Equal(expectedConfig.VectorStoreId, agent.Definition.ToolResources.FileSearch?.VectorStoreIds.SingleOrDefault());
        Assert.Equal(expectedConfig.CodeInterpreterFileIds, agent.Definition.ToolResources.CodeInterpreter?.FileIds);
    }

    private async Task<OpenAIAssistantAgent> CreateAgentAsync()
    {
        OpenAIAssistantDefinition definition = new("testmodel");

        this.SetupResponse(HttpStatusCode.OK, definition);

        var clientProvider = this.CreateTestClient();
        var assistantClient = clientProvider.Client.GetAssistantClient();
        var assistantCreationOptions = new AssistantCreationOptions();
        var model = await assistantClient.CreateAssistantAsync("testmodel", assistantCreationOptions);

        return new OpenAIAssistantAgent(model, assistantClient)
        {
            Kernel = this._emptyKernel
        };
    }

    private OpenAIClientProvider CreateTestClient(bool targetAzure = false)
        => targetAzure ?
            OpenAIClientProvider.ForAzureOpenAI(apiKey: new ApiKeyCredential("fakekey"), endpoint: new Uri("https://localhost"), this._httpClient) :
            OpenAIClientProvider.ForOpenAI(apiKey: new ApiKeyCredential("fakekey"), endpoint: null, this._httpClient);

    private void SetupResponse(HttpStatusCode statusCode, string content) =>
        this._messageHandlerStub.SetupResponses(statusCode, content);

    private void SetupResponse(HttpStatusCode statusCode, OpenAIAssistantDefinition definition) =>
        this._messageHandlerStub.SetupResponses(statusCode, OpenAIAssistantResponseContent.AssistantDefinition(definition));

    private void SetupResponse(HttpStatusCode statusCode, OpenAIAssistantCapabilities capabilities, PromptTemplateConfig templateConfig) =>
        this._messageHandlerStub.SetupResponses(statusCode, OpenAIAssistantResponseContent.AssistantDefinition(capabilities, templateConfig));

    private void SetupResponses(HttpStatusCode statusCode, params string[] content) =>
        this._messageHandlerStub.SetupResponses(statusCode, content);

    private sealed class MyPlugin
    {
        [KernelFunction]
        public void MyFunction(int index)
        { }
    }

    /// <summary>
    /// Helper class for testing AIFunction behavior.
    /// </summary>
    private sealed class TestAIFunction : AIFunction
    {
        public TestAIFunction(string name, string description = "")
        {
            this.Name = name;
            this.Description = description;
        }

        public override string Name { get; }

        public override string Description { get; }

        protected override ValueTask<object?> InvokeCoreAsync(AIFunctionArguments? arguments = null, CancellationToken cancellationToken = default)
        {
            return ValueTask.FromResult<object?>("Test result");
        }
    }
}
#pragma warning restore CS0419 // Ambiguous reference in cref attribute


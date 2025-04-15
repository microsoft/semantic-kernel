// Copyright (c) Microsoft. All rights reserved.
using System;
using System.ClientModel;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
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
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.CreateAsync"/>
    /// for an agent with only required properties defined.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentCreationEmptyAsync()
    {
        // Arrange
        OpenAIAssistantDefinition definition = new("testmodel");

        // Act and Assert
        await this.VerifyAgentCreationAsync(definition);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.CreateAsync"/>
    /// for an agent with name, instructions, and description.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentCreationPropertiesAsync()
    {
        // Arrange
        OpenAIAssistantDefinition definition =
            new("testmodel")
            {
                Name = "testname",
                Description = "testdescription",
                Instructions = "testinstructions",
            };

        // Act and Assert
        await this.VerifyAgentCreationAsync(definition);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.CreateAsync"/>
    /// for an agent with name, instructions, and description from a template.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentCreationDefaultTemplateAsync()
    {
        // Arrange
        PromptTemplateConfig templateConfig =
            new("test instructions")
            {
                Name = "testname",
                Description = "testdescription",
            };

        OpenAIAssistantCapabilities capabilities = new("testmodel");

        // Act and Assert
        await this.VerifyAgentTemplateAsync(capabilities, templateConfig, new KernelPromptTemplateFactory());
        await Assert.ThrowsAsync<KernelException>(async () => await this.VerifyAgentTemplateAsync(capabilities, templateConfig, new HandlebarsPromptTemplateFactory()));
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.CreateAsync"/>
    /// for an agent with code-interpreter enabled.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentCreationWithCodeInterpreterAsync()
    {
        // Arrange
        OpenAIAssistantDefinition definition =
            new("testmodel")
            {
                EnableCodeInterpreter = true,
            };

        // Act and Assert
        await this.VerifyAgentCreationAsync(definition);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.CreateAsync"/>
    /// for an agent with code-interpreter files.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentCreationWithCodeInterpreterFilesAsync()
    {
        // Arrange
        OpenAIAssistantDefinition definition =
            new("testmodel")
            {
                EnableCodeInterpreter = true,
                CodeInterpreterFileIds = ["file1", "file2"],
            };

        // Act and Assert
        await this.VerifyAgentCreationAsync(definition);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.CreateAsync"/>
    /// for an agent with a file-search and no vector-store
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentCreationWithFileSearchAsync()
    {
        // Arrange
        OpenAIAssistantDefinition definition =
            new("testmodel")
            {
                EnableFileSearch = true,
            };

        // Act and Assert
        await this.VerifyAgentCreationAsync(definition);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.CreateAsync"/>
    /// for an agent with a vector-store-id (for file-search).
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentCreationWithVectorStoreAsync()
    {
        // Arrange
        OpenAIAssistantDefinition definition =
            new("testmodel")
            {
                EnableFileSearch = true,
                VectorStoreId = "#vs1",
            };

        // Act and Assert
        await this.VerifyAgentCreationAsync(definition);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.CreateAsync"/>
    /// for an agent with metadata.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentCreationWithMetadataAsync()
    {
        // Arrange
        OpenAIAssistantDefinition definition =
            new("testmodel")
            {
                Metadata = new Dictionary<string, string>()
                {
                    { "a", "1" },
                    { "b", "2" },
                },
            };

        // Act and Assert
        await this.VerifyAgentCreationAsync(definition);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.CreateAsync"/>
    /// for an agent with json-response mode enabled.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentCreationWithJsonResponseAsync()
    {
        // Arrange
        OpenAIAssistantDefinition definition =
            new("testmodel")
            {
                EnableJsonResponse = true,
            };

        // Act and Assert
        await this.VerifyAgentCreationAsync(definition);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.CreateAsync"/>
    /// for an agent with temperature defined.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentCreationWithTemperatureAsync()
    {
        // Arrange
        OpenAIAssistantDefinition definition =
            new("testmodel")
            {
                Temperature = 2.0F,
            };

        // Act and Assert
        await this.VerifyAgentCreationAsync(definition);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.CreateAsync"/>
    /// for an agent with topP defined.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentCreationWithTopPAsync()
    {
        // Arrange
        OpenAIAssistantDefinition definition =
            new("testmodel")
            {
                TopP = 2.0F,
            };

        // Act and Assert
        await this.VerifyAgentCreationAsync(definition);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.CreateAsync"/>
    /// for an agent with empty execution settings.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentCreationWithEmptyExecutionOptionsAsync()
    {
        // Arrange
        OpenAIAssistantDefinition definition =
            new("testmodel")
            {
                ExecutionOptions = new OpenAIAssistantExecutionOptions(),
            };

        // Act and Assert
        await this.VerifyAgentCreationAsync(definition);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.CreateAsync"/>
    /// for an agent with populated execution settings.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentCreationWithExecutionOptionsAsync()
    {
        // Arrange
        OpenAIAssistantDefinition definition =
            new("testmodel")
            {
                ExecutionOptions =
                    new()
                    {
                        MaxCompletionTokens = 100,
                        ParallelToolCallsEnabled = false,
                    }
            };

        // Act and Assert
        await this.VerifyAgentCreationAsync(definition);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.CreateAsync"/>
    /// for an agent with execution settings and meta-data.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentCreationWithEmptyExecutionOptionsAndMetadataAsync()
    {
        // Arrange
        OpenAIAssistantDefinition definition =
            new("testmodel")
            {
                ExecutionOptions = new(),
                Metadata = new Dictionary<string, string>()
                {
                    { "a", "1" },
                    { "b", "2" },
                },
            };

        // Act and Assert
        await this.VerifyAgentCreationAsync(definition);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.RetrieveAsync"/>.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentRetrievalAsync()
    {
        // Arrange
        OpenAIAssistantDefinition definition = new("testmodel");

        this.SetupResponse(HttpStatusCode.OK, definition);

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.RetrieveAsync(
                this.CreateTestProvider(),
                "#id",
                this._emptyKernel);

        // Act and Assert
        ValidateAgentDefinition(agent, definition);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.RetrieveAsync"/>.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentRetrievalWithFactoryAsync()
    {
        // Arrange
        OpenAIAssistantDefinition definition = new("testmodel");

        this.SetupResponse(HttpStatusCode.OK, definition);

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.RetrieveAsync(
                this.CreateTestProvider(),
                "#id",
                this._emptyKernel,
                [],
                new KernelPromptTemplateFactory());

        // Act and Assert
        ValidateAgentDefinition(agent, definition);
    }

    /// <summary>
    /// Verify the deletion of agent via <see cref="OpenAIAssistantAgent.DeleteAsync"/>.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentDeleteAsync()
    {
        // Arrange
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();
        this.SetupResponse(HttpStatusCode.OK, OpenAIAssistantResponseContent.DeleteAgent);

        // Act
        bool isDeleted = await agent.DeleteAsync();

        // Assert
        Assert.True(isDeleted);
    }

    /// <summary>
    /// Verify the creating a thread via <see cref="OpenAIAssistantAgent"/>.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentCreateThreadAsync()
    {
        // Arrange
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();

        this.SetupResponse(HttpStatusCode.OK, OpenAIAssistantResponseContent.CreateThread);

        // Act
        string threadId = await agent.CreateThreadAsync();
        // Assert
        Assert.NotNull(threadId);

        // Arrange
        this.SetupResponse(HttpStatusCode.OK, OpenAIAssistantResponseContent.CreateThread);
        // Act
        threadId = await agent.CreateThreadAsync(new OpenAIThreadCreationOptions());
        // Assert
        Assert.NotNull(threadId);
    }

    /// <summary>
    /// Verify the deleting a thread via <see cref="OpenAIAssistantAgent.DeleteThreadAsync"/>.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentDeleteThreadAsync()
    {
        // Arrange
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();

        this.SetupResponse(HttpStatusCode.OK, OpenAIAssistantResponseContent.DeleteThread);

        // Act
        bool isDeleted = await agent.DeleteThreadAsync("threadid");
        // Assert
        Assert.True(isDeleted);
    }

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
        Assert.IsType<TextContent>(messages[0].Items[0]);

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
        Assert.IsType<TextContent>(messages[0].Message.Items[0]);
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
        Assert.IsType<TextContent>(messages[0].Message.Items[0]);
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
        AgentResponseItem<StreamingChatMessageContent>[] messages = await agent.InvokeStreamingAsync(new ChatMessageContent(AuthorRole.User, "Hi")).ToArrayAsync();

        // Assert
        Assert.Equal(3, messages.Length);
        var combinedMessage = string.Concat(messages.Select(x => x.Message.Content));
        Assert.Equal("Hello, how can I help you?", combinedMessage);
    }

    /// <summary>
    /// Verify direct invocation of <see cref="OpenAIAssistantAgent"/>.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentInvokeAsync()
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

        // Act
        ChatMessageContent[] messages = await agent.InvokeAsync("threadid").ToArrayAsync();

        // Assert
        Assert.Single(messages);
        Assert.Single(messages[0].Items);
        Assert.IsType<TextContent>(messages[0].Items[0]);
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
        Assert.NotNull(messages[0].Items.SingleOrDefault(c => c is TextContent));
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
    /// Verify message retrieval via <see cref="OpenAIAssistantAgent.GetThreadMessagesAsync(string, System.Threading.CancellationToken)"/>.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentAddThreadMessagesAsync()
    {
        // Arrange: Create agent
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();
        // Arrange: Setup messages
        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.GetTextMessage());

        // Act (no exception)
        await agent.AddChatMessageAsync(agent.Id, new ChatMessageContent(AuthorRole.User, "hi"));
        Assert.Empty(this._messageHandlerStub.ResponseQueue);
    }

    /// <summary>
    /// Verify message retrieval via <see cref="OpenAIAssistantAgent.GetThreadMessagesAsync(string, System.Threading.CancellationToken)"/>.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentGetThreadMessagesAsync()
    {
        // Arrange: Create agent
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();

        // Arrange: Setup messages
        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.ListMessagesPageMore,
            OpenAIAssistantResponseContent.ListMessagesPageMore,
            OpenAIAssistantResponseContent.ListMessagesPageFinal);

        // Act: Get messages
        ChatMessageContent[] messages = await agent.GetThreadMessagesAsync("threadid").ToArrayAsync();

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
    public async Task VerifyOpenAIAssistantAgentListDefinitionAsync()
    {
        // Arrange
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();

        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.ListAgentsPageMore,
            OpenAIAssistantResponseContent.ListAgentsPageMore,
            OpenAIAssistantResponseContent.ListAgentsPageFinal);

        // Act
        var messages =
            await OpenAIAssistantAgent.ListDefinitionsAsync(
                this.CreateTestProvider()).ToArrayAsync();
        // Assert
        Assert.Equal(7, messages.Length);

        // Arrange
        this.SetupResponses(
            HttpStatusCode.OK,
            OpenAIAssistantResponseContent.ListAgentsPageMore,
            OpenAIAssistantResponseContent.ListAgentsPageFinal);

        // Act
        messages =
            await OpenAIAssistantAgent.ListDefinitionsAsync(
                this.CreateTestProvider()).ToArrayAsync();
        // Assert
        Assert.Equal(4, messages.Length);
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
        Assert.IsType<TextContent>(messages[0].Items[0]);
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

    private async Task VerifyAgentCreationAsync(OpenAIAssistantDefinition definition)
    {
        this.SetupResponse(HttpStatusCode.OK, definition);

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                this.CreateTestProvider(),
                definition,
                this._emptyKernel);

        ValidateAgentDefinition(agent, definition);
    }

    private async Task VerifyAgentTemplateAsync(
        OpenAIAssistantCapabilities capabilities,
        PromptTemplateConfig templateConfig,
        IPromptTemplateFactory templateFactory)
    {
        this.SetupResponse(HttpStatusCode.OK, capabilities, templateConfig);

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateFromTemplateAsync(
                this.CreateTestProvider(),
                capabilities,
                this._emptyKernel,
                [],
                templateConfig,
                templateFactory);

        ValidateAgentDefinition(agent, capabilities, templateConfig);
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

    private Task<OpenAIAssistantAgent> CreateAgentAsync()
    {
        OpenAIAssistantDefinition definition = new("testmodel");

        this.SetupResponse(HttpStatusCode.OK, definition);

        return
            OpenAIAssistantAgent.CreateAsync(
                this.CreateTestProvider(),
                definition,
                this._emptyKernel);
    }

    private OpenAIClientProvider CreateTestProvider(bool targetAzure = false)
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
}
#pragma warning restore CS0419 // Ambiguous reference in cref attribute


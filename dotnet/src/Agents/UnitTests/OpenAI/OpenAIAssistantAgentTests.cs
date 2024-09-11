// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Assistants;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Unit testing of <see cref="OpenAIAssistantAgent"/>.
/// </summary>
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

        this.SetupResponse(HttpStatusCode.OK, ResponseContent.CreateAgentPayload(definition));

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.RetrieveAsync(
                this._emptyKernel,
                this.CreateTestConfiguration(),
                "#id");

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
        // Assert
        Assert.False(agent.IsDeleted);

        // Arrange
        this.SetupResponse(HttpStatusCode.OK, ResponseContent.DeleteAgent);

        // Act
        await agent.DeleteAsync();
        // Assert
        Assert.True(agent.IsDeleted);

        // Act
        await agent.DeleteAsync(); // Doesn't throw
        // Assert
        Assert.True(agent.IsDeleted);
        await Assert.ThrowsAsync<KernelException>(() => agent.AddChatMessageAsync("threadid", new(AuthorRole.User, "test")));
        await Assert.ThrowsAsync<KernelException>(() => agent.InvokeAsync("threadid").ToArrayAsync().AsTask());
    }

    /// <summary>
    /// Verify the deletion of agent via <see cref="OpenAIAssistantAgent.DeleteAsync"/>.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentCreateThreadAsync()
    {
        // Arrange
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();

        this.SetupResponse(HttpStatusCode.OK, ResponseContent.CreateThread);

        // Act
        string threadId = await agent.CreateThreadAsync();
        // Assert
        Assert.NotNull(threadId);

        // Arrange
        this.SetupResponse(HttpStatusCode.OK, ResponseContent.CreateThread);

        // Act
        threadId = await agent.CreateThreadAsync(new());
        // Assert
        Assert.NotNull(threadId);
    }

    /// <summary>
    /// Verify complex chat interaction across multiple states.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentChatTextMessageAsync()
    {
        // Arrange
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();

        this.SetupResponses(
            HttpStatusCode.OK,
            ResponseContent.CreateThread,
            ResponseContent.CreateRun,
            ResponseContent.CompletedRun,
            ResponseContent.MessageSteps,
            ResponseContent.GetTextMessage);

        AgentGroupChat chat = new();

        // Act
        ChatMessageContent[] messages = await chat.InvokeAsync(agent).ToArrayAsync();

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
            ResponseContent.CreateThread,
            ResponseContent.CreateRun,
            ResponseContent.CompletedRun,
            ResponseContent.MessageSteps,
            ResponseContent.GetTextMessageWithAnnotation);

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
            ResponseContent.CreateThread,
            ResponseContent.CreateRun,
            ResponseContent.CompletedRun,
            ResponseContent.MessageSteps,
            ResponseContent.GetImageMessage);

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
            ResponseContent.CreateThread,
            ResponseContent.CreateRun,
            ResponseContent.CompletedRun,
            ResponseContent.MessageSteps,
            ResponseContent.GetTextMessage);

        AgentGroupChat chat = new();

        // Act
        ChatMessageContent[] messages = await chat.InvokeAsync(agent).ToArrayAsync();
        // Assert
        Assert.Single(messages);

        // Arrange: Setup messages
        this.SetupResponses(
            HttpStatusCode.OK,
            ResponseContent.ListMessagesPageMore,
            ResponseContent.ListMessagesPageMore,
            ResponseContent.ListMessagesPageFinal);

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
            ResponseContent.CreateThread,
            ResponseContent.CreateRun,
            ResponseContent.CompletedRun,
            ResponseContent.MessageSteps,
            ResponseContent.GetTextMessage);
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
            ResponseContent.ListAgentsPageMore,
            ResponseContent.ListAgentsPageMore,
            ResponseContent.ListAgentsPageFinal);

        // Act
        var messages =
            await OpenAIAssistantAgent.ListDefinitionsAsync(
                this.CreateTestConfiguration()).ToArrayAsync();
        // Assert
        Assert.Equal(7, messages.Length);

        // Arrange
        this.SetupResponses(
            HttpStatusCode.OK,
            ResponseContent.ListAgentsPageMore,
            ResponseContent.ListAgentsPageFinal);

        // Act
        messages =
            await OpenAIAssistantAgent.ListDefinitionsAsync(
                this.CreateTestConfiguration()).ToArrayAsync();
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
            ResponseContent.CreateThread,
            ResponseContent.CreateRun,
            ResponseContent.PendingRun,
            ResponseContent.ToolSteps,
            ResponseContent.ToolResponse,
            ResponseContent.CompletedRun,
            ResponseContent.MessageSteps,
            ResponseContent.GetTextMessage);

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
        this.SetupResponse(HttpStatusCode.OK, ResponseContent.CreateAgentPayload(definition));

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                this._emptyKernel,
                this.CreateTestConfiguration(),
                definition);

        ValidateAgentDefinition(agent, definition);
    }

    private static void ValidateAgentDefinition(OpenAIAssistantAgent agent, OpenAIAssistantDefinition sourceDefinition)
    {
        // Verify fundamental state
        Assert.NotNull(agent);
        Assert.NotNull(agent.Id);
        Assert.False(agent.IsDeleted);
        Assert.NotNull(agent.Definition);
        Assert.Equal(sourceDefinition.ModelId, agent.Definition.ModelId);

        // Verify core properties
        Assert.Equal(sourceDefinition.Instructions ?? string.Empty, agent.Instructions);
        Assert.Equal(sourceDefinition.Name ?? string.Empty, agent.Name);
        Assert.Equal(sourceDefinition.Description ?? string.Empty, agent.Description);

        // Verify options
        Assert.Equal(sourceDefinition.Temperature, agent.Definition.Temperature);
        Assert.Equal(sourceDefinition.TopP, agent.Definition.TopP);
        Assert.Equal(sourceDefinition.ExecutionOptions?.MaxCompletionTokens, agent.Definition.ExecutionOptions?.MaxCompletionTokens);
        Assert.Equal(sourceDefinition.ExecutionOptions?.MaxPromptTokens, agent.Definition.ExecutionOptions?.MaxPromptTokens);
        Assert.Equal(sourceDefinition.ExecutionOptions?.ParallelToolCallsEnabled, agent.Definition.ExecutionOptions?.ParallelToolCallsEnabled);
        Assert.Equal(sourceDefinition.ExecutionOptions?.TruncationMessageCount, agent.Definition.ExecutionOptions?.TruncationMessageCount);

        // Verify tool definitions
        int expectedToolCount = 0;

        bool hasCodeInterpreter = false;
        if (sourceDefinition.EnableCodeInterpreter)
        {
            hasCodeInterpreter = true;
            ++expectedToolCount;
        }

        Assert.Equal(hasCodeInterpreter, agent.Tools.OfType<CodeInterpreterToolDefinition>().Any());

        bool hasFileSearch = false;
        if (sourceDefinition.EnableFileSearch)
        {
            hasFileSearch = true;
            ++expectedToolCount;
        }

        Assert.Equal(hasFileSearch, agent.Tools.OfType<FileSearchToolDefinition>().Any());

        Assert.Equal(expectedToolCount, agent.Tools.Count);

        // Verify metadata
        Assert.NotNull(agent.Definition.Metadata);
        if (sourceDefinition.ExecutionOptions == null)
        {
            Assert.Equal(sourceDefinition.Metadata ?? new Dictionary<string, string>(), agent.Definition.Metadata);
        }
        else // Additional metadata present when execution options are defined
        {
            Assert.Equal((sourceDefinition.Metadata?.Count ?? 0) + 1, agent.Definition.Metadata.Count);

            if (sourceDefinition.Metadata != null)
            {
                foreach (var (key, value) in sourceDefinition.Metadata)
                {
                    string? targetValue = agent.Definition.Metadata[key];
                    Assert.NotNull(targetValue);
                    Assert.Equal(value, targetValue);
                }
            }
        }

        // Verify detail definition
        Assert.Equal(sourceDefinition.VectorStoreId, agent.Definition.VectorStoreId);
        Assert.Equal(sourceDefinition.CodeInterpreterFileIds, agent.Definition.CodeInterpreterFileIds);
    }

    private Task<OpenAIAssistantAgent> CreateAgentAsync()
    {
        OpenAIAssistantDefinition definition = new("testmodel");

        this.SetupResponse(HttpStatusCode.OK, ResponseContent.CreateAgentPayload(definition));

        return
            OpenAIAssistantAgent.CreateAsync(
                this._emptyKernel,
                this.CreateTestConfiguration(),
                definition);
    }

    private OpenAIClientProvider CreateTestConfiguration(bool targetAzure = false)
        => targetAzure ?
            OpenAIClientProvider.ForAzureOpenAI(apiKey: "fakekey", endpoint: new Uri("https://localhost"), this._httpClient) :
            OpenAIClientProvider.ForOpenAI(apiKey: "fakekey", endpoint: null, this._httpClient);

    private void SetupResponse(HttpStatusCode statusCode, string content)
    {
        this._messageHandlerStub.ResponseToReturn =
            new(statusCode)
            {
                Content = new StringContent(content)
            };
    }

    private void SetupResponses(HttpStatusCode statusCode, params string[] content)
    {
        foreach (var item in content)
        {
#pragma warning disable CA2000 // Dispose objects before losing scope
            this._messageHandlerStub.ResponseQueue.Enqueue(
                new(statusCode)
                {
                    Content = new StringContent(item)
                });
#pragma warning restore CA2000 // Dispose objects before losing scope
        }
    }

    private sealed class MyPlugin
    {
        [KernelFunction]
        public void MyFunction(int index)
        { }
    }

    private static class ResponseContent
    {
        public static string CreateAgentPayload(OpenAIAssistantDefinition definition)
        {
            StringBuilder builder = new();
            builder.AppendLine("{");
            builder.AppendLine(@"  ""id"": ""asst_abc123"",");
            builder.AppendLine(@"  ""object"": ""assistant"",");
            builder.AppendLine(@"  ""created_at"": 1698984975,");
            builder.AppendLine(@$"  ""name"": ""{definition.Name}"",");
            builder.AppendLine(@$"  ""description"": ""{definition.Description}"",");
            builder.AppendLine(@$"  ""instructions"": ""{definition.Instructions}"",");
            builder.AppendLine(@$"  ""model"": ""{definition.ModelId}"",");

            bool hasCodeInterpreter = definition.EnableCodeInterpreter;
            bool hasCodeInterpreterFiles = (definition.CodeInterpreterFileIds?.Count ?? 0) > 0;
            bool hasFileSearch = definition.EnableFileSearch;
            if (!hasCodeInterpreter && !hasFileSearch)
            {
                builder.AppendLine(@"  ""tools"": [],");
            }
            else
            {
                builder.AppendLine(@"  ""tools"": [");

                if (hasCodeInterpreter)
                {
                    builder.Append(@$"  {{ ""type"": ""code_interpreter"" }}{(hasFileSearch ? "," : string.Empty)}");
                }

                if (hasFileSearch)
                {
                    builder.AppendLine(@"  { ""type"": ""file_search"" }");
                }

                builder.AppendLine("    ],");
            }

            if (!hasCodeInterpreterFiles && !hasFileSearch)
            {
                builder.AppendLine(@"  ""tool_resources"": {},");
            }
            else
            {
                builder.AppendLine(@"  ""tool_resources"": {");

                if (hasCodeInterpreterFiles)
                {
                    string fileIds = string.Join(",", definition.CodeInterpreterFileIds!.Select(fileId => "\"" + fileId + "\""));
                    builder.AppendLine(@$"  ""code_interpreter"": {{ ""file_ids"": [{fileIds}] }}{(hasFileSearch ? "," : string.Empty)}");
                }

                if (hasFileSearch)
                {
                    builder.AppendLine(@$"  ""file_search"": {{ ""vector_store_ids"": [""{definition.VectorStoreId}""] }}");
                }

                builder.AppendLine("    },");
            }

            if (definition.Temperature.HasValue)
            {
                builder.AppendLine(@$"  ""temperature"": {definition.Temperature},");
            }

            if (definition.TopP.HasValue)
            {
                builder.AppendLine(@$"  ""top_p"": {definition.TopP},");
            }

            bool hasExecutionOptions = definition.ExecutionOptions != null;
            int metadataCount = (definition.Metadata?.Count ?? 0);
            if (metadataCount == 0 && !hasExecutionOptions)
            {
                builder.AppendLine(@"  ""metadata"": {}");
            }
            else
            {
                int index = 0;
                builder.AppendLine(@"  ""metadata"": {");

                if (hasExecutionOptions)
                {
                    string serializedExecutionOptions = JsonSerializer.Serialize(definition.ExecutionOptions);
                    builder.AppendLine(@$"    ""{OpenAIAssistantAgent.OptionsMetadataKey}"": ""{JsonEncodedText.Encode(serializedExecutionOptions)}""{(metadataCount > 0 ? "," : string.Empty)}");
                }

                if (metadataCount > 0)
                {
                    foreach (var (key, value) in definition.Metadata!)
                    {
                        builder.AppendLine(@$"    ""{key}"": ""{value}""{(index < metadataCount - 1 ? "," : string.Empty)}");
                        ++index;
                    }
                }

                builder.AppendLine("  }");
            }

            builder.AppendLine("}");

            return builder.ToString();
        }

        public const string CreateAgentWithEverything =
            """
            {
              "tool_resources": {
                "file_search": { "vector_store_ids": ["#vs"] }
              },
            }
            """;

        public const string DeleteAgent =
          """
            {
              "id": "asst_abc123",
              "object": "assistant.deleted",
              "deleted": true
            }
            """;

        public const string CreateThread =
            """
            {
              "id": "thread_abc123",
              "object": "thread",
              "created_at": 1699012949,
              "metadata": {}
            }
            """;

        public const string CreateRun =
            """
            {
              "id": "run_abc123",
              "object": "thread.run",
              "created_at": 1699063290,
              "assistant_id": "asst_abc123",
              "thread_id": "thread_abc123",
              "status": "queued",
              "started_at": 1699063290,
              "expires_at": null,
              "cancelled_at": null,
              "failed_at": null,
              "completed_at": 1699063291,
              "last_error": null,
              "model": "gpt-4-turbo",
              "instructions": null,
              "tools": [],
              "file_ids": [],
              "metadata": {},
              "usage": null,
              "temperature": 1
            }
            """;

        public const string PendingRun =
            """
            {
              "id": "run_abc123",
              "object": "thread.run",
              "created_at": 1699063290,
              "assistant_id": "asst_abc123",
              "thread_id": "thread_abc123",
              "status": "requires_action",
              "started_at": 1699063290,
              "expires_at": null,
              "cancelled_at": null,
              "failed_at": null,
              "completed_at": 1699063291,
              "last_error": null,
              "model": "gpt-4-turbo",
              "instructions": null,
              "tools": [],
              "file_ids": [],
              "metadata": {},
              "usage": null,
              "temperature": 1
            }
            """;

        public const string CompletedRun =
            """
            {
              "id": "run_abc123",
              "object": "thread.run",
              "created_at": 1699063290,
              "assistant_id": "asst_abc123",
              "thread_id": "thread_abc123",
              "status": "completed",
              "started_at": 1699063290,
              "expires_at": null,
              "cancelled_at": null,
              "failed_at": null,
              "completed_at": 1699063291,
              "last_error": null,
              "model": "gpt-4-turbo",
              "instructions": null,
              "tools": [],
              "file_ids": [],
              "metadata": {},
              "usage": null,
              "temperature": 1
            }
            """;

        public const string MessageSteps =
            """
            {
              "object": "list",
              "data": [
                {
                  "id": "step_abc123",
                  "object": "thread.run.step",
                  "created_at": 1699063291,
                  "run_id": "run_abc123",
                  "assistant_id": "asst_abc123",
                  "thread_id": "thread_abc123",
                  "type": "message_creation",
                  "status": "completed",
                  "cancelled_at": null,
                  "completed_at": 1699063291,
                  "expired_at": null,
                  "failed_at": null,
                  "last_error": null,
                  "step_details": {
                    "type": "message_creation",
                    "message_creation": {
                      "message_id": "msg_abc123"
                    }
                  },
                  "usage": {
                    "prompt_tokens": 123,
                    "completion_tokens": 456,
                    "total_tokens": 579
                  }
                }
              ],
              "first_id": "step_abc123",
              "last_id": "step_abc456",
              "has_more": false
            }
            """;

        public const string ToolSteps =
            """
            {
              "object": "list",
              "data": [
                {
                  "id": "step_abc987",
                  "object": "thread.run.step",
                  "created_at": 1699063291,
                  "run_id": "run_abc123",
                  "assistant_id": "asst_abc123",
                  "thread_id": "thread_abc123",
                  "type": "tool_calls",
                  "status": "in_progress",
                  "cancelled_at": null,
                  "completed_at": 1699063291,
                  "expired_at": null,
                  "failed_at": null,
                  "last_error": null,
                  "step_details": {
                    "type": "tool_calls",
                    "tool_calls": [
                     {
                        "id": "tool_1",
                        "type": "function",
                        "function": {
                            "name": "MyPlugin-MyFunction",
                            "arguments": "{ \"index\": 3 }",
                            "output": "test"
                        }
                     }
                    ]
                  },
                  "usage": {
                    "prompt_tokens": 123,
                    "completion_tokens": 456,
                    "total_tokens": 579
                  }
                }
              ],
              "first_id": "step_abc123",
              "last_id": "step_abc456",
              "has_more": false
            }
            """;

        public const string ToolResponse = "{ }";

        public const string GetImageMessage =
            """
            {
              "id": "msg_abc123",
              "object": "thread.message",
              "created_at": 1699017614,
              "thread_id": "thread_abc123",
              "role": "user",
              "content": [
                {
                  "type": "image_file",
                  "image_file": {
                    "file_id": "file_123"
                  }
                }
              ],
              "assistant_id": "asst_abc123",
              "run_id": "run_abc123"
            }
            """;

        public const string GetTextMessage =
            """
            {
              "id": "msg_abc123",
              "object": "thread.message",
              "created_at": 1699017614,
              "thread_id": "thread_abc123",
              "role": "user",
              "content": [
                {
                  "type": "text",
                  "text": {
                    "value": "How does AI work? Explain it in simple terms.",
                    "annotations": []
                  }
                }
              ],
              "assistant_id": "asst_abc123",
              "run_id": "run_abc123"
            }
            """;

        public const string GetTextMessageWithAnnotation =
            """
            {
              "id": "msg_abc123",
              "object": "thread.message",
              "created_at": 1699017614,
              "thread_id": "thread_abc123",
              "role": "user",
              "content": [
                {
                  "type": "text",
                  "text": {
                    "value": "How does AI work? Explain it in simple terms.**f1",
                    "annotations": [
                        {
                            "type": "file_citation",
                            "text": "**f1",
                            "file_citation": {
                                "file_id": "file_123",
                                "quote": "does"
                            },
                            "start_index": 3,
                            "end_index": 6
                        }
                    ]
                  }
                }
              ],
              "assistant_id": "asst_abc123",
              "run_id": "run_abc123"
            }
            """;

        public const string ListAgentsPageMore =
            """
            {
              "object": "list",
              "data": [
                {
                  "id": "asst_abc123",
                  "object": "assistant",
                  "created_at": 1698982736,
                  "name": "Coding Tutor",
                  "description": null,
                  "model": "gpt-4-turbo",
                  "instructions": "You are a helpful assistant designed to make me better at coding!",
                  "tools": [],
                  "metadata": {}
                },
                {
                  "id": "asst_abc456",
                  "object": "assistant",
                  "created_at": 1698982718,
                  "name": "My Assistant",
                  "description": null,
                  "model": "gpt-4-turbo",
                  "instructions": "You are a helpful assistant designed to make me better at coding!",
                  "tools": [],
                  "metadata": {}
                },
                {
                  "id": "asst_abc789",
                  "object": "assistant",
                  "created_at": 1698982643,
                  "name": null,
                  "description": null,
                  "model": "gpt-4-turbo",
                  "instructions": null,
                  "tools": [],
                  "metadata": {}
                }
              ],
              "first_id": "asst_abc123",
              "last_id": "asst_abc789",
              "has_more": true
            }
            """;

        public const string ListAgentsPageFinal =
            """
            {
              "object": "list",
              "data": [
                {
                  "id": "asst_abc789",
                  "object": "assistant",
                  "created_at": 1698982736,
                  "name": "Coding Tutor",
                  "description": null,
                  "model": "gpt-4-turbo",
                  "instructions": "You are a helpful assistant designed to make me better at coding!",
                  "tools": [],
                  "metadata": {}
                }           
              ],
              "first_id": "asst_abc789",
              "last_id": "asst_abc789",
              "has_more": false
            }
            """;

        public const string ListMessagesPageMore =
            """
            {
              "object": "list",
              "data": [
                {
                  "id": "msg_abc123",
                  "object": "thread.message",
                  "created_at": 1699016383,
                  "thread_id": "thread_abc123",
                  "role": "user",
                  "content": [
                    {
                      "type": "text",
                      "text": {
                        "value": "How does AI work? Explain it in simple terms.",
                        "annotations": []
                      }
                    }
                  ],
                  "file_ids": [],
                  "assistant_id": null,
                  "run_id": null,
                  "metadata": {}
                },
                {
                  "id": "msg_abc456",
                  "object": "thread.message",
                  "created_at": 1699016383,
                  "thread_id": "thread_abc123",
                  "role": "user",
                  "content": [
                    {
                      "type": "text",
                      "text": {
                        "value": "Hello, what is AI?",
                        "annotations": []
                      }
                    }
                  ],
                  "file_ids": [
                    "file-abc123"
                  ],
                  "assistant_id": null,
                  "run_id": null,
                  "metadata": {}
                }
              ],
              "first_id": "msg_abc123",
              "last_id": "msg_abc456",
              "has_more": true
            }
            """;

        public const string ListMessagesPageFinal =
            """
            {
              "object": "list",
              "data": [
                {
                  "id": "msg_abc789",
                  "object": "thread.message",
                  "created_at": 1699016383,
                  "thread_id": "thread_abc123",
                  "role": "user",
                  "content": [
                    {
                      "type": "text",
                      "text": {
                        "value": "How does AI work? Explain it in simple terms.",
                        "annotations": []
                      }
                    }
                  ],
                  "file_ids": [],
                  "assistant_id": null,
                  "run_id": null,
                  "metadata": {}
                }
              ],
              "first_id": "msg_abc789",
              "last_id": "msg_abc789",
              "has_more": false
            }
            """;
    }
}

// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Azure.AI.OpenAI.Assistants;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
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
        OpenAIAssistantDefinition definition =
            new()
            {
                ModelId = "testmodel",
            };

        this.SetupResponse(HttpStatusCode.OK, ResponseContent.CreateAgentSimple);

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                this._emptyKernel,
                this.CreateTestConfiguration(targetAzure: true, useVersion: true),
                definition);

        Assert.NotNull(agent);
        Assert.NotNull(agent.Id);
        Assert.Null(agent.Instructions);
        Assert.Null(agent.Name);
        Assert.Null(agent.Description);
        Assert.False(agent.IsDeleted);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.CreateAsync"/>
    /// for an agent with optional properties defined.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentCreationPropertiesAsync()
    {
        OpenAIAssistantDefinition definition =
            new()
            {
                ModelId = "testmodel",
                Name = "testname",
                Description = "testdescription",
                Instructions = "testinstructions",
            };

        this.SetupResponse(HttpStatusCode.OK, ResponseContent.CreateAgentFull);

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                this._emptyKernel,
                this.CreateTestConfiguration(),
                definition);

        Assert.NotNull(agent);
        Assert.NotNull(agent.Id);
        Assert.NotNull(agent.Instructions);
        Assert.NotNull(agent.Name);
        Assert.NotNull(agent.Description);
        Assert.False(agent.IsDeleted);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.CreateAsync"/>
    /// for an agent that has all properties defined..
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentCreationEverythingAsync()
    {
        OpenAIAssistantDefinition definition =
            new()
            {
                ModelId = "testmodel",
                EnableCodeInterpreter = true,
                EnableRetrieval = true,
                FileIds = ["#1", "#2"],
                Metadata = new Dictionary<string, string>() { { "a", "1" } },
            };

        this.SetupResponse(HttpStatusCode.OK, ResponseContent.CreateAgentWithEverything);

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                this._emptyKernel,
                this.CreateTestConfiguration(),
                definition);

        Assert.NotNull(agent);
        Assert.Equal(2, agent.Tools.Count);
        Assert.True(agent.Tools.OfType<CodeInterpreterToolDefinition>().Any());
        Assert.True(agent.Tools.OfType<RetrievalToolDefinition>().Any());
        Assert.NotEmpty(agent.FileIds);
        Assert.NotEmpty(agent.Metadata);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.RetrieveAsync"/>.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentRetrieveAsync()
    {
        this.SetupResponse(HttpStatusCode.OK, ResponseContent.CreateAgentSimple);

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.RetrieveAsync(
                this._emptyKernel,
                this.CreateTestConfiguration(),
                "#id");

        Assert.NotNull(agent);
        Assert.NotNull(agent.Id);
        Assert.Null(agent.Instructions);
        Assert.Null(agent.Name);
        Assert.Null(agent.Description);
        Assert.False(agent.IsDeleted);
    }

    /// <summary>
    /// Verify the deletion of agent via <see cref="OpenAIAssistantAgent.DeleteAsync"/>.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentDeleteAsync()
    {
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();
        Assert.False(agent.IsDeleted);

        this.SetupResponse(HttpStatusCode.OK, ResponseContent.DeleteAgent);

        await agent.DeleteAsync();
        Assert.True(agent.IsDeleted);

        await agent.DeleteAsync(); // Doesn't throw
        Assert.True(agent.IsDeleted);
    }

    /// <summary>
    /// Verify complex chat interaction across multiple states.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentChatTextMessageAsync()
    {
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();

        this.SetupResponses(
            HttpStatusCode.OK,
            ResponseContent.CreateThread,
            ResponseContent.CreateRun,
            ResponseContent.CompletedRun,
            ResponseContent.MessageSteps,
            ResponseContent.GetTextMessage);

        AgentGroupChat chat = new();
        ChatMessageContent[] messages = await chat.InvokeAsync(agent).ToArrayAsync();
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
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();

        this.SetupResponses(
            HttpStatusCode.OK,
            ResponseContent.CreateThread,
            ResponseContent.CreateRun,
            ResponseContent.CompletedRun,
            ResponseContent.MessageSteps,
            ResponseContent.GetTextMessageWithAnnotation);

        AgentGroupChat chat = new();
        ChatMessageContent[] messages = await chat.InvokeAsync(agent).ToArrayAsync();
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
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();

        this.SetupResponses(
            HttpStatusCode.OK,
            ResponseContent.CreateThread,
            ResponseContent.CreateRun,
            ResponseContent.CompletedRun,
            ResponseContent.MessageSteps,
            ResponseContent.GetImageMessage);

        AgentGroupChat chat = new();
        ChatMessageContent[] messages = await chat.InvokeAsync(agent).ToArrayAsync();
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
        // Create agent
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
        ChatMessageContent[] messages = await chat.InvokeAsync(agent).ToArrayAsync();
        Assert.Single(messages);

        // Setup messages
        this.SetupResponses(
            HttpStatusCode.OK,
            ResponseContent.ListMessagesPageMore,
            ResponseContent.ListMessagesPageMore,
            ResponseContent.ListMessagesPageFinal);

        // Get messages and verify
        messages = await chat.GetChatMessagesAsync(agent).ToArrayAsync();
        Assert.Equal(5, messages.Length);
    }

    /// <summary>
    /// Verify complex chat interaction across multiple states.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentAddMessagesAsync()
    {
        // Create agent
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
        ChatMessageContent[] messages = await chat.InvokeAsync(agent).ToArrayAsync();
        Assert.Single(messages);

        chat.Add(new ChatMessageContent(AuthorRole.User, "hi"));

        messages = await chat.GetChatMessagesAsync().ToArrayAsync();
        Assert.Equal(2, messages.Length);
    }

    /// <summary>
    /// Verify ability to list agent definitions.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentListDefinitionAsync()
    {
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();

        this.SetupResponses(
            HttpStatusCode.OK,
            ResponseContent.ListAgentsPageMore,
            ResponseContent.ListAgentsPageMore,
            ResponseContent.ListAgentsPageFinal);

        var messages =
            await OpenAIAssistantAgent.ListDefinitionsAsync(
                this.CreateTestConfiguration()).ToArrayAsync();
        Assert.Equal(7, messages.Length);

        this.SetupResponses(
            HttpStatusCode.OK,
            ResponseContent.ListAgentsPageMore,
            ResponseContent.ListAgentsPageMore);

        messages =
            await OpenAIAssistantAgent.ListDefinitionsAsync(
                this.CreateTestConfiguration(),
                maxResults: 4).ToArrayAsync();
        Assert.Equal(4, messages.Length);
    }

    /// <summary>
    /// Verify ability to list agent definitions.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentWithFunctionCallAsync()
    {
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
        ChatMessageContent[] messages = await chat.InvokeAsync(agent).ToArrayAsync();
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

    private Task<OpenAIAssistantAgent> CreateAgentAsync()
    {
        OpenAIAssistantDefinition definition =
            new()
            {
                ModelId = "testmodel",
            };

        this.SetupResponse(HttpStatusCode.OK, ResponseContent.CreateAgentSimple);

        return
            OpenAIAssistantAgent.CreateAsync(
                this._emptyKernel,
                this.CreateTestConfiguration(),
                definition);
    }

    private OpenAIAssistantConfiguration CreateTestConfiguration(bool targetAzure = false, bool useVersion = false)
    {
        return new(apiKey: "fakekey", endpoint: targetAzure ? "https://localhost" : null)
        {
            HttpClient = this._httpClient,
            Version = useVersion ? AssistantsClientOptions.ServiceVersion.V2024_02_15_Preview : null,
        };
    }

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
        public const string CreateAgentSimple =
            """
            {
              "id": "asst_abc123",
              "object": "assistant",
              "created_at": 1698984975,
              "name": null,
              "description": null,
              "model": "gpt-4-turbo",
              "instructions": null,
              "tools": [],
              "file_ids": [],
              "metadata": {}
            }
            """;

        public const string CreateAgentFull =
            """
            {
              "id": "asst_abc123",
              "object": "assistant",
              "created_at": 1698984975,
              "name": "testname",
              "description": "testdescription",
              "model": "gpt-4-turbo",
              "instructions": "testinstructions",
              "tools": [],
              "file_ids": [],
              "metadata": {}
            }
            """;

        public const string CreateAgentWithEverything =
            """
            {
              "id": "asst_abc123",
              "object": "assistant",
              "created_at": 1698984975,
              "name": null,
              "description": null,
              "model": "gpt-4-turbo",
              "instructions": null,
              "tools": [
                {
                  "type": "code_interpreter"
                },
                {
                  "type": "retrieval"
                }
              ],
              "file_ids": ["#1", "#2"],
              "metadata": {"a": "1"}
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
                  "file_ids": [],
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
                  "file_ids": [],
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
                  "file_ids": [],
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
                  "file_ids": [],
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

// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
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
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.CreateAsync"/>.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentCreationAsync()
    {
        OpenAIAssistantDefinition definition =
            new()
            {
                Model = "testmodel",
            };

        this.SetupResponse(HttpStatusCode.OK, ResponseContent.CreateAgentSimple);

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                this._emptyKernel,
                this.CreateTestConfiguration(),
                definition);

        Assert.NotNull(agent);
        Assert.NotNull(agent.Id);
        Assert.Null(agent.Instructions);
        Assert.Null(agent.Name);
        Assert.Null(agent.Description);
        Assert.False(agent.IsDeleted);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="OpenAIAssistantAgent.RestoreAsync"/>.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentRestoreAsync()
    {
        this.SetupResponse(HttpStatusCode.OK, ResponseContent.CreateAgentSimple);

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.RestoreAsync(
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
    }

    /// <summary>
    /// Verify the deletion of agent via <see cref="OpenAIAssistantAgent.DeleteAsync"/>.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentChatAsync()
    {
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();

        this.SetupResponses(
            HttpStatusCode.OK,
            ResponseContent.CreateThread,
            ResponseContent.CreateRun,
            ResponseContent.CompletedRun,
            ResponseContent.MessageSteps,
            ResponseContent.GetMessage);

        AgentGroupChat chat = new();
        var messages = await chat.InvokeAsync(agent).ToArrayAsync();
        Assert.Single(messages);

        this.SetupResponses(
            HttpStatusCode.OK,
            ResponseContent.ListMessagesPageMore,
            ResponseContent.ListMessagesPageMore,
            ResponseContent.ListMessagesPageFinal);

        messages = await chat.GetChatMessagesAsync(agent).ToArrayAsync();
        Assert.Equal(5, messages.Length);
    }

    /// <summary>
    /// Verify the deletion of agent via <see cref="OpenAIAssistantAgent.ListAsync"/>.
    /// </summary>
    [Fact]
    public async Task VerifyOpenAIAssistantAgentListAsync()
    {
        OpenAIAssistantAgent agent = await this.CreateAgentAsync();

        this.SetupResponses(
            HttpStatusCode.OK,
            ResponseContent.ListAgentsPageMore,
            ResponseContent.ListAgentsPageMore,
            ResponseContent.ListAgentsPageFinal);

        var messages =
            await OpenAIAssistantAgent.ListAsync(
                this.CreateTestConfiguration()).ToArrayAsync();
        Assert.Equal(7, messages.Length);

        this.SetupResponses(
            HttpStatusCode.OK,
            ResponseContent.ListAgentsPageMore,
            ResponseContent.ListAgentsPageMore);

        messages =
            await OpenAIAssistantAgent.ListAsync(
                this.CreateTestConfiguration(),
                maxResults: 4).ToArrayAsync();
        Assert.Equal(4, messages.Length);
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
        this._emptyKernel = Kernel.CreateBuilder().Build();
    }

    private Task<OpenAIAssistantAgent> CreateAgentAsync()
    {
        OpenAIAssistantDefinition definition =
            new()
            {
                Model = "testmodel",
            };

        this.SetupResponse(HttpStatusCode.OK, ResponseContent.CreateAgentSimple);

        return
            OpenAIAssistantAgent.CreateAsync(
                this._emptyKernel,
                this.CreateTestConfiguration(),
                definition);
    }

    private OpenAIAssistantConfiguration CreateTestConfiguration()
    {
        return new("fakekey")
        {
            HttpClient = this._httpClient,
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
#pragma warning disable CA2000 // Dispose objects before losing scope $$$
            this._messageHandlerStub.ResponseQueue.Enqueue(
                new(statusCode)
                {
                    Content = new StringContent(item)
                });
#pragma warning restore CA2000 // Dispose objects before losing scope
        }
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

        public const string GetMessage =
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
              "file_ids": [],
              "assistant_id": "asst_abc123",
              "run_id": "run_abc123",
              "metadata": {}
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

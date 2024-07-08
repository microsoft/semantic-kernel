// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Unit testing of <see cref="OpenAIVectorStore"/>.
/// </summary>
public sealed class OpenAIVectorStoreTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private readonly HttpClient _httpClient;

    /// <summary>
    /// %%%
    /// </summary>
    [Fact]
    public void VerifyOpenAIVectorStoreInitialization()
    {
        //this.SetupResponse(HttpStatusCode.OK, ResponseContent.CreateAgentSimple);

        OpenAIVectorStore store = new("#vs1", this.CreateTestConfiguration());
        Assert.Equal("#vs1", store.VectorStoreId);
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
    public OpenAIVectorStoreTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._httpClient = new HttpClient(this._messageHandlerStub, disposeHandler: false);
    }

    private OpenAIServiceConfiguration CreateTestConfiguration(bool targetAzure = false)
        => targetAzure ?
            OpenAIServiceConfiguration.ForAzureOpenAI(apiKey: "fakekey", endpoint: new Uri("https://localhost"), this._httpClient) :
            OpenAIServiceConfiguration.ForOpenAI(apiKey: "fakekey", endpoint: null, this._httpClient);

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
                  "type": "file_search"
                }
              ],
              "tool_resources": {
                "file_search": {
                    "vector_store_ids": ["#vs"]
                }
              },
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

// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using OpenAI.Assistants;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Mock response payloads for <see cref="OpenAIAssistantAgent"/>.
/// </summary>
internal static class OpenAIAssistantResponseContent
{
    /// <summary>
    /// Setup the response content for the <see cref="HttpMessageHandlerStub"/>.
    /// </summary>
    public static void SetupResponse(this HttpMessageHandlerStub messageHandlerStub, HttpStatusCode statusCode, string content)
    {
        messageHandlerStub.ResponseToReturn =
            new HttpResponseMessage(statusCode)
            {
                Content = new StringContent(content)
            };
    }

    /// <summary>
    /// Setup the response content for the <see cref="HttpMessageHandlerStub"/>.
    /// </summary>
    public static void SetupResponses(this HttpMessageHandlerStub messageHandlerStub, HttpStatusCode statusCode, params string[] content)
    {
        foreach (var item in content)
        {
#pragma warning disable CA2000 // Dispose objects before losing scope
            messageHandlerStub.ResponseQueue.Enqueue(
                new(statusCode)
                {
                    Content = new StreamContent(new MemoryStream(Encoding.UTF8.GetBytes(item)))
                });
#pragma warning restore CA2000 // Dispose objects before losing scope
        }
    }

    private const string AssistantId = "asst_abc123";
    private const string ThreadId = "thread_abc123";
    private const string RunId = "run_abc123";
    private const string MessageId = "msg_abc123";
    private const string StepId = "step_abc123";

    #region Assistant

    /// <summary>
    /// The response for creating or querying an assistant definition.
    /// </summary>
    public static string AssistantDefinition(OpenAIAssistantCapabilities capabilities, PromptTemplateConfig templateConfig) =>
        AssistantDefinition(templateConfig.Name, templateConfig.Template, templateConfig.Description, capabilities);

    /// <summary>
    /// The response for creating or querying an assistant definition.
    /// </summary>
    public static string AssistantDefinition(OpenAIAssistantDefinition definition) =>
        AssistantDefinition(definition.Name, definition.Instructions, definition.Description, definition);

    /// <summary>
    /// The response for creating or querying an assistant definition.
    /// </summary>
    public static string AssistantDefinition(
        string? name,
        string? instructions,
        string? description,
        OpenAIAssistantCapabilities capabilities)
    {
        StringBuilder builder = new();
        builder.AppendLine("{");
        builder.AppendLine(@$"  ""id"": ""{AssistantId}"",");
        builder.AppendLine(@"  ""object"": ""assistant"",");
        builder.AppendLine(@"  ""created_at"": 1698984975,");
        builder.AppendLine(@$"  ""name"": ""{name}"",");
        builder.AppendLine(@$"  ""description"": ""{description}"",");
        builder.AppendLine(@$"  ""instructions"": ""{instructions}"",");
        builder.AppendLine(@$"  ""model"": ""{capabilities.ModelId}"",");

        bool hasCodeInterpreter = capabilities.EnableCodeInterpreter;
        bool hasCodeInterpreterFiles = (capabilities.CodeInterpreterFileIds?.Count ?? 0) > 0;
        bool hasFileSearch = capabilities.EnableFileSearch;
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
                string fileIds = string.Join(",", capabilities.CodeInterpreterFileIds!.Select(fileId => "\"" + fileId + "\""));
                builder.AppendLine(@$"  ""code_interpreter"": {{ ""file_ids"": [{fileIds}] }}{(hasFileSearch ? "," : string.Empty)}");
            }

            if (hasFileSearch && capabilities.VectorStoreId != null)
            {
                builder.AppendLine(@$"  ""file_search"": {{ ""vector_store_ids"": [""{capabilities.VectorStoreId}""] }}");
            }

            builder.AppendLine("    },");
        }

        if (capabilities.Temperature.HasValue)
        {
            builder.AppendLine(@$"  ""temperature"": {capabilities.Temperature},");
        }

        if (capabilities.TopP.HasValue)
        {
            builder.AppendLine(@$"  ""top_p"": {capabilities.TopP},");
        }

        bool hasExecutionOptions = capabilities.ExecutionOptions != null;
        int metadataCount = (capabilities.Metadata?.Count ?? 0);
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
                string serializedExecutionOptions = JsonSerializer.Serialize(capabilities.ExecutionOptions);
                builder.AppendLine(@$"    ""{OpenAIAssistantAgent.OptionsMetadataKey}"": ""{JsonEncodedText.Encode(serializedExecutionOptions)}""{(metadataCount > 0 ? "," : string.Empty)}");
            }

            if (metadataCount > 0)
            {
                foreach (var (key, value) in capabilities.Metadata!)
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

    /// <summary>
    /// The response for creating or querying an assistant definition.
    /// </summary>
    public static string AssistantDefinition(
        string modelId,
        string? name = null,
        string? description = null,
        string? instructions = null,
        bool enableCodeInterpreter = false,
        IReadOnlyList<string>? codeInterpreterFileIds = null,
        bool enableFileSearch = false,
        string? vectorStoreId = null,
        float? temperature = null,
        float? topP = null,
        AssistantResponseFormat? responseFormat = null,
        IReadOnlyDictionary<string, string>? metadata = null)
    {
        StringBuilder builder = new();
        builder.AppendLine("{");
        builder.AppendLine(@$"  ""id"": ""{AssistantId}"",");
        builder.AppendLine(@"  ""object"": ""assistant"",");
        builder.AppendLine(@"  ""created_at"": 1698984975,");
        builder.AppendLine(@$"  ""name"": ""{name}"",");
        builder.AppendLine(@$"  ""description"": ""{description}"",");
        builder.AppendLine(@$"  ""instructions"": ""{instructions}"",");
        builder.AppendLine(@$"  ""model"": ""{modelId}"",");

        bool hasCodeInterpreterFiles = (codeInterpreterFileIds?.Count ?? 0) > 0;
        bool hasCodeInterpreter = enableCodeInterpreter || hasCodeInterpreterFiles;
        bool hasFileSearch = enableFileSearch || vectorStoreId != null;
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
                string fileIds = string.Join(",", codeInterpreterFileIds!.Select(fileId => "\"" + fileId + "\""));
                builder.AppendLine(@$"  ""code_interpreter"": {{ ""file_ids"": [{fileIds}] }}{(hasFileSearch ? "," : string.Empty)}");
            }

            if (hasFileSearch && vectorStoreId != null)
            {
                builder.AppendLine(@$"  ""file_search"": {{ ""vector_store_ids"": [""{vectorStoreId}""] }}");
            }

            builder.AppendLine("    },");
        }

        if (temperature.HasValue)
        {
            builder.AppendLine(@$"  ""temperature"": {temperature},");
        }

        if (topP.HasValue)
        {
            builder.AppendLine(@$"  ""top_p"": {topP},");
        }
        int metadataCount = (metadata?.Count ?? 0);
        if (metadataCount == 0)
        {
            builder.AppendLine(@"  ""metadata"": {}");
        }
        else
        {
            int index = 0;
            builder.AppendLine(@"  ""metadata"": {");

            if (metadataCount > 0)
            {
                foreach (var (key, value) in metadata!)
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

    public const string DeleteAgent =
        $$$"""
        {
            "id": "{{{AssistantId}}}",
            "object": "assistant.deleted",
            "deleted": true
        }
        """;

    public const string CreateThread =
        $$$"""
        {
            "id": "{{{ThreadId}}}",
            "object": "thread",
            "created_at": 1699012949,
            "metadata": {}
        }
        """;

    public const string DeleteThread =
        $$$"""
        {
            "id": "{{{ThreadId}}}",
            "object": "thread.deleted",
            "deleted": true
        }
        """;

    public const string ToolResponse = "{ }";

    public const string GetImageMessage =
        $$$"""
        {
            "id": "{{{MessageId}}}",
            "object": "thread.message",
            "created_at": 1699017614,
            "thread_id": "{{{ThreadId}}}",
            "role": "user",
            "content": [
            {
                "type": "image_file",
                "image_file": {
                "file_id": "file_123"
                }
            }
            ],
            "assistant_id": "{{{AssistantId}}}",
            "run_id": "{{{RunId}}}"
        }
        """;

    public static string GetTextMessage(string text = "test") =>
        $$$"""
        {
            "id": "{{{MessageId}}}",
            "object": "thread.message",
            "created_at": 1699017614,
            "thread_id": "{{{ThreadId}}}",
            "role": "user",
            "content": [
            {
                "type": "text",
                "text": {
                "value": "{{{text}}}",
                "annotations": []
                }
            }
            ],
            "assistant_id": "{{{AssistantId}}}",
            "run_id": "{{{RunId}}}"
        }
        """;

    public const string GetTextMessageWithAnnotation =
        $$$"""
        {
            "id": "{{{MessageId}}}",
            "object": "thread.message",
            "created_at": 1699017614,
            "thread_id": "{{{ThreadId}}}",
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
            "assistant_id": "{{{AssistantId}}}",
            "run_id": "{{{RunId}}}"
        }
        """;

    public const string ListAgentsPageMore =
        $$$"""
        {
            "object": "list",
            "data": [
            {
                "id": "{{{AssistantId}}}",
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
            "first_id": "{{{AssistantId}}}",
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
        $$$"""
        {
            "object": "list",
            "data": [
            {
                "id": "{{{MessageId}}}",
                "object": "thread.message",
                "created_at": 1699016383,
                "thread_id": "{{{ThreadId}}}",
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
                "thread_id": "{{{ThreadId}}}",
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
            "first_id": "{{{MessageId}}}",
            "last_id": "msg_abc456",
            "has_more": true
        }
        """;

    public const string ListMessagesPageFinal =
        $$$"""
        {
            "object": "list",
            "data": [
            {
                "id": "msg_abc789",
                "object": "thread.message",
                "created_at": 1699016383,
                "thread_id": "{{{ThreadId}}}",
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

    public static string UploadFile =
        """
        {
          "id": "file-abc123",
          "object": "file",
          "bytes": 120000,
          "created_at": 1677610602,
          "filename": "test.txt",
          "purpose": "assistants"
        }
        """;

    public static string DeleteFile =
        """
        {
          "id": "file-abc123",
          "object": "file",
          "deleted": true
        }
        """;

    public static string CreateVectorStore =
        """
        {
          "id": "vs_abc123",
          "object": "vector_store",
          "created_at": 1699061776,
          "name": "test store",
          "bytes": 139920,
          "file_counts": {
            "in_progress": 0,
            "completed": 3,
            "failed": 0,
            "cancelled": 0,
            "total": 3
          }
        }      
        """;

    public static string DeleteVectorStore =
        """
        {
          "id": "vs-abc123",
          "object": "vector_store.deleted",
          "deleted": true
        }
        """;

    #endregion

    /// <summary>
    /// Response payloads for a "regular" assistant run.
    /// </summary>
    public static class Run
    {
        public const string CreateRun =
            $$$"""
            {
              "id": "{{{RunId}}}",
              "object": "thread.run",
              "created_at": 1699063290,
              "assistant_id": "{{{AssistantId}}}",
              "thread_id": "{{{ThreadId}}}",
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
            $$$"""
            {
              "id": "{{{RunId}}}",
              "object": "thread.run",
              "created_at": 1699063290,
              "assistant_id": "{{{AssistantId}}}",
              "thread_id": "{{{ThreadId}}}",
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
            $$$"""
            {
              "id": "{{{RunId}}}",
              "object": "thread.run",
              "created_at": 1699063290,
              "assistant_id": "{{{AssistantId}}}",
              "thread_id": "{{{ThreadId}}}",
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
            $$$"""
            {
              "object": "list",
              "data": [
                {
                  "id": "{{{StepId}}}",
                  "object": "thread.run.step",
                  "created_at": 1699063291,
                  "run_id": "{{{RunId}}}",
                  "assistant_id": "{{{AssistantId}}}",
                  "thread_id": "{{{ThreadId}}}",
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
                      "message_id": "{{{MessageId}}}"
                    }
                  },
                  "usage": {
                    "prompt_tokens": 123,
                    "completion_tokens": 456,
                    "total_tokens": 579
                  }
                }
              ],
              "first_id": "{{{StepId}}}",
              "last_id": "step_abc456",
              "has_more": false
            }
            """;

        public const string ToolSteps =
            $$$"""
            {
              "object": "list",
              "data": [
                {
                  "id": "step_abc987",
                  "object": "thread.run.step",
                  "created_at": 1699063291,
                  "run_id": "{{{RunId}}}",
                  "assistant_id": "{{{AssistantId}}}",
                  "thread_id": "{{{ThreadId}}}",
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
              "first_id": "{{{StepId}}}",
              "last_id": "step_abc456",
              "has_more": false
            }
            """;
    }

    /// <summary>
    /// Response payloads for a streaming assistant run.
    /// </summary>
    public static class Streaming
    {
        public static string Response(params string[] eventPayloads)
        {
            StringBuilder builder = new();

            foreach (string payload in eventPayloads)
            {
                builder.Append(payload);
                builder.AppendLine();
                builder.AppendLine();
            }

            return builder.ToString();
        }

        public const string Done =
            """
            event: thread.done
            data: [DONE]
            """;

        public static string CreateRun(string eventType)
        {
            int? createdAt = null;
            int? startedAt = null;
            int? completedAt = null;
            int? expiresAt = null;
            string? status = null;

            switch (eventType)
            {
                case "created":
                    status = "created";
                    createdAt = 1725978974;
                    break;
                case "queued":
                    status = "queued";
                    createdAt = 1725978974;
                    break;
                case "in_progress":
                    status = "in_progress";
                    createdAt = 1725978974;
                    startedAt = 1725978975;
                    expiresAt = 1725979576;
                    break;
                case "completed":
                    status = "completed";
                    createdAt = 1725978974;
                    startedAt = 1725978975;
                    expiresAt = 1725979576;
                    completedAt = 1725978976;
                    break;
            }

            Assert.NotNull(status);

            return
                CreateEvent(
                    $"thread.run.{eventType}",
                    $$$"""
                    {
                      "id": "{{{RunId}}}",
                      "object": "thread.run",
                      "assistant_id": "{{{AssistantId}}}",
                      "thread_id": "{{{ThreadId}}}",
                      "status": "{{{status}}}",
                      "created_at": {{{ParseTimestamp(createdAt)}}},
                      "started_at": {{{ParseTimestamp(startedAt)}}},
                      "expires_at": {{{ParseTimestamp(expiresAt)}}},
                      "completed_at": {{{ParseTimestamp(completedAt)}}},
                      "required_action": null,
                      "model": "gpt-4o-mini",
                      "instructions": "test",
                      "tools": [],
                      "metadata": {},
                      "temperature": 1.0,
                      "top_p": 1.0,
                      "truncation_strategy": { "type": "auto" },
                      "incomplete_details": null,
                      "usage": null,
                      "response_format": "auto",
                      "tool_choice": "auto",
                      "parallel_tool_calls": true
                    }
                    """);
        }

        public static string DeltaMessage(string text) =>
                CreateEvent(
                    "thread.message.delta",
                    $$$"""
                    {
                      "id": "{{{MessageId}}}",
                      "object": "thread.message.delta",
                      "delta": {
                        "content": [
                          {
                            "index": 0,
                            "type": "text",
                            "text": { "value": "{{{text}}}", "annotations": [] }
                          }
                        ]
                      }
                    }
                    """);

        private static string ParseTimestamp(int? timestamp)
        {
            if (timestamp.HasValue)
            {
                return timestamp.Value.ToString();
            }

            return "0";
        }

        private static string CreateEvent(string eventType, string data) =>
            $"""
            event: {eventType}
            data: {data.Replace("\n", string.Empty).Replace("\r", string.Empty)}
            """;
    }
}

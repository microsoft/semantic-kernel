// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Handoff;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Orchestration;

/// <summary>
/// Tests for the <see cref="HandoffOrchestration"/> class.
/// </summary>
public class HandoffOrchestrationTests : IDisposable
{
    private readonly List<IDisposable> _disposables;

    /// <summary>
    /// Initializes a new instance of the <see cref="HandoffOrchestrationTests"/> class.
    /// </summary>
    public HandoffOrchestrationTests()
    {
        this._disposables = [];
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        foreach (IDisposable disposable in this._disposables)
        {
            disposable.Dispose();
        }
        GC.SuppressFinalize(this);
    }

    [Fact]
    public async Task HandoffOrchestrationWithSingleAgentAsync()
    {
        // Arrange
        ChatCompletionAgent mockAgent1 =
            this.CreateMockAgent(
                "Agent1",
                "Test Agent",
                Responses.Message("Final response"));

        // Act: Create and execute the orchestration
        string response = await ExecuteOrchestrationAsync(OrchestrationHandoffs.StartWith(mockAgent1), mockAgent1);

        // Assert
        Assert.Equal("Final response", response);
    }

    [Fact]
    public async Task HandoffOrchestrationWithMultipleAgentsAsync()
    {
        // Arrange
        ChatCompletionAgent mockAgent1 =
            this.CreateMockAgent(
                "Agent1",
                "Test Agent",
                Responses.Handoff("Agent2"));
        ChatCompletionAgent mockAgent2 =
            this.CreateMockAgent(
                "Agent2",
                "Test Agent",
                Responses.Result("Final response"));
        ChatCompletionAgent mockAgent3 =
            this.CreateMockAgent(
                "Agent3",
                "Test Agent",
                Responses.Message("Wrong response"));

        // Act: Create and execute the orchestration
        string response = await ExecuteOrchestrationAsync(
            OrchestrationHandoffs
                .StartWith(mockAgent1)
                .Add(mockAgent1, mockAgent2, mockAgent3),
            mockAgent1,
            mockAgent2,
            mockAgent3);

        // Assert
        Assert.Equal("Final response", response);
    }

    private static async Task<string> ExecuteOrchestrationAsync(OrchestrationHandoffs handoffs, params Agent[] mockAgents)
    {
        // Arrange
        await using InProcessRuntime runtime = new();
        await runtime.StartAsync();

        HandoffOrchestration orchestration = new(handoffs, mockAgents);

        // Act
        const string InitialInput = "123";
        OrchestrationResult<string> result = await orchestration.InvokeAsync(InitialInput, runtime);

        // Assert
        Assert.NotNull(result);

        // Act
        string response = await result.GetValueAsync(TimeSpan.FromSeconds(10));
        await runtime.RunUntilIdleAsync();

        return response;
    }

    private ChatCompletionAgent CreateMockAgent(string name, string description, string response)
    {
        HttpMessageHandlerStub messageHandlerStub =
            new()
            {
                ResponseToReturn = new HttpResponseMessage
                {
                    StatusCode = System.Net.HttpStatusCode.OK,
                    Content = new StringContent(response),
                },
            };
        HttpClient httpClient = new(messageHandlerStub, disposeHandler: false);

        this._disposables.Add(messageHandlerStub);
        this._disposables.Add(httpClient);

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.AddOpenAIChatCompletion("gpt-test", "mykey", orgId: null, serviceId: null, httpClient);
        Kernel kernel = builder.Build();

        ChatCompletionAgent mockAgent1 =
            new()
            {
                Name = name,
                Description = description,
                Kernel = kernel,
            };

        return mockAgent1;
    }

    private static class Responses
    {
        public static string Message(string content) =>
            $$$"""            
            {
              "id": "chat-123",
              "object": "chat.completion",
              "created": 1699482945,
              "model": "gpt-4.1",
              "choices": [
                {
                  "index": 0,
                  "message": {
                    "role": "assistant",
                    "content": "{{{content}}}",
                    "tool_calls":[]
                  }
                }
              ],
              "usage": {
                "prompt_tokens": 52,
                "completion_tokens": 1,
                "total_tokens": 53
              }
            }      
            """;

        public static string Handoff(string agentName) =>
            $$$"""            
            {
              "id": "chat-123",
              "object": "chat.completion",
              "created": 1699482945,
              "model": "gpt-4.1",
              "choices": [
                {
                  "index": 0,
                  "message": {
                    "role": "assistant",
                    "content": null,
                    "tool_calls":[{
                        "id": "1",
                        "type": "function",
                        "function": {
                          "name": "{{{HandoffInvocationFilter.HandoffPlugin}}}-transfer_to_{{{agentName}}}",
                          "arguments": "{}"
                        }
                      }
                    ]
                  }
                }
              ],
              "usage": {
                "prompt_tokens": 52,
                "completion_tokens": 1,
                "total_tokens": 53
              }
            }      
            """;

        public static string Result(string summary) =>
            $$$"""            
            {
              "id": "chat-123",
              "object": "chat.completion",
              "created": 1699482945,
              "model": "gpt-4.1",
              "choices": [
                {
                  "index": 0,
                  "message": {
                    "role": "assistant",
                    "content": null,
                    "tool_calls":[{
                        "id": "1",
                        "type": "function",
                        "function": {
                          "name": "{{{HandoffInvocationFilter.HandoffPlugin}}}-end_task_with_summary",
                          "arguments": "{ \"summary\": \"{{{summary}}}\" }"
                        }
                      }
                    ]
                  }
                }
              ]
            }      
            """;
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Tests for the <see cref="OpenAIResponseAgent"/> class.
/// </summary>
public sealed class OpenAIResponseAgentTests : BaseOpenAIResponseClientTest
{
    /// <summary>
    /// Tests that the constructor verifies parameters and throws <see cref="ArgumentNullException"/> when necessary.
    /// </summary>
    [Fact]
    public void ConstructorShouldVerifyParams()
    {
        // Arrange & Act & Assert
        Assert.Throws<ArgumentNullException>(() => new OpenAIResponseAgent(null!));
    }

    /// <summary>
    /// Tests that the OpenAIResponseAgent.InvokeAsync verifies parameters and throws <see cref="ArgumentNullException"/> when necessary.
    /// </summary>
    [Fact]
    public void InvokeShouldVerifyParams()
    {
        // Arrange
        var agent = new OpenAIResponseAgent(this.Client);
        string nullString = null!;
        ChatMessageContent nullMessage = null!;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => agent.InvokeAsync(nullString));
        Assert.Throws<ArgumentNullException>(() => agent.InvokeAsync(nullMessage));
    }

    /// <summary>
    /// Tests that the OpenAIResponseAgent.InvokeAsync verifies parameters and throws <see cref="ArgumentNullException"/> when necessary.
    /// </summary>
    [Fact]
    public async Task VerifyInvokeAsync()
    {
        // Arrange
        this.MessageHandlerStub.ResponsesToReturn.Add(
            new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StringContent(InvokeResponse) }
        );
        var agent = new OpenAIResponseAgent(this.Client)
        {
            Name = "ResponseAgent",
            Instructions = "Answer all queries in English and French.",
        };

        // Act
        var responseItems = agent.InvokeAsync("What is the capital of France?");

        // Assert
        Assert.NotNull(responseItems);
        var items = await responseItems!.ToListAsync<AgentResponseItem<ChatMessageContent>>();
        Assert.Single(items);
        Assert.Equal("The capital of France is Paris.\n\nLa capitale de la France est Paris.", items[0].Message.Content);
    }

    #region private
    private const string InvokeResponse =
        """
        {
          "id": "resp_67e8f5cf761c8191aab763d1e901e3410bbdc4b8da506cd2",
          "object": "response",
          "created_at": 1743320527,
          "status": "completed",
          "error": null,
          "incomplete_details": null,
          "instructions": "Answer all queries in English and French.",
          "max_output_tokens": null,
          "model": "gpt-4o-2024-08-06",
          "output": [
            {
              "type": "message",
              "id": "msg_67e8f5cfbe688191a428ed9869c39fea0bbdc4b8da506cd2",
              "status": "completed",
              "role": "assistant",
              "content": [
                {
                  "type": "output_text",
                  "text": "The capital of France is Paris.\n\nLa capitale de la France est Paris.",
                  "annotations": []
                }
              ]
            }
          ],
          "parallel_tool_calls": true,
          "previous_response_id": null,
          "reasoning": {
            "effort": null,
            "generate_summary": null
          },
          "store": true,
          "temperature": 1.0,
          "text": {
            "format": {
              "type": "text"
            }
          },
          "tool_choice": "auto",
          "tools": [],
          "top_p": 1.0,
          "truncation": "disabled",
          "usage": {
            "input_tokens": 26,
            "input_tokens_details": {
              "cached_tokens": 0
            },
            "output_tokens": 16,
            "output_tokens_details": {
              "reasoning_tokens": 0
            },
            "total_tokens": 42
          },
          "user": "ResponseAgent",
          "metadata": {}
        }
        """;
    #endregion
}

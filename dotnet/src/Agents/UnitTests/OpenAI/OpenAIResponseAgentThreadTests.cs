// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Tests for the <see cref="OpenAIResponseAgentThread"/> class.
/// </summary>
public sealed class OpenAIResponseAgentThreadTests : BaseOpenAIResponseClientTest
{
    /// <summary>
    /// Tests that the constructor verifies parameters and throws <see cref="ArgumentNullException"/> when necessary.
    /// </summary>
    [Fact]
    public void ConstructorShouldVerifyParams()
    {
        // Arrange & Act & Assert
        Assert.Throws<ArgumentNullException>(() => new OpenAIResponseAgentThread(null!));
        Assert.Throws<ArgumentNullException>(() => new OpenAIResponseAgentThread(null!, "threadId"));
        Assert.Throws<ArgumentNullException>(() => new OpenAIResponseAgentThread(this.Client, responseId: null!));

        var agentThread = new OpenAIResponseAgentThread(this.Client);
        Assert.NotNull(agentThread);
    }

    /// <summary>
    /// Tests that the constructor for resuming a thread uses the provided parameters.
    /// </summary>
    [Fact]
    public void ConstructorForResumingThreadShouldUseParams()
    {
        // Arrange & Act
        var agentThread = new OpenAIResponseAgentThread(this.Client, "threadId");

        // Assert
        Assert.NotNull(agentThread);
        Assert.Equal("threadId", agentThread.Id);
    }

    /// <summary>
    /// Verify <see cref="OpenAIResponseAgentThread.GetMessagesAsync(System.Threading.CancellationToken)"/> returned when store is disabled.
    /// </summary>
    [Fact]
    public async Task VerifyGetMessagesWhenThreadIsUnusedAsync()
    {
        // Arrange
        var thread = new OpenAIResponseAgentThread(this.Client);

        // Act
        var messages = thread.GetMessagesAsync();

        // Assert
        Assert.NotNull(messages);
        var messagesList = await messages!.ToListAsync<ChatMessageContent>();
        Assert.Empty(messagesList);
    }

    /// <summary>
    /// Verify <see cref="OpenAIResponseAgentThread.GetMessagesAsync(System.Threading.CancellationToken)"/> returned when store is disabled.
    /// </summary>
    [Fact]
    public async Task VerifyGetMessagesWhenStoreEnabledAsync()
    {
        // Arrange
        this.MessageHandlerStub.ResponsesToReturn.Add(
             new HttpResponseMessage(System.Net.HttpStatusCode.OK) { Content = new StringContent(MessagesResponse) }
         );
        var responseId = "resp_67e8ff743ea08191b085bea42b4d83e809a3a922c4f4221b";
        var thread = new OpenAIResponseAgentThread(this.Client, responseId: responseId);

        // Act
        var messages = thread.GetMessagesAsync();

        // Assert
        Assert.NotNull(messages);
        var messagesList = await messages!.ToListAsync<ChatMessageContent>();
        Assert.Equal(3, messagesList.Count);
    }

    #region private
    private const string MessagesResponse =
        """
        {
          "object": "list",
          "data": [
            {
              "type": "message",
              "id": "msg_67e8ff7445408191af5d6f4a87a9d3fe09a3a922c4f4221b",
              "status": "completed",
              "role": "user",
              "content": [
                {
                  "type": "input_text",
                  "text": "Explain why this is funny."
                }
              ]
            },
            {
              "type": "message",
              "id": "msg_67e8ff73be188191b871e41c2816355209a3a922c4f4221b",
              "status": "completed",
              "role": "assistant",
              "content": [
                {
                  "type": "output_text",
                  "text": "Why don't skeletons fight each other?\n\nThey don't have the guts!",
                  "annotations": []
                }
              ]
            },
            {
              "type": "message",
              "id": "msg_67e8ff7258a081919e7964ac7b344bc909a3a922c4f4221b",
              "status": "completed",
              "role": "user",
              "content": [
                {
                  "type": "input_text",
                  "text": "Tell me a joke?"
                }
              ]
            }
          ],
          "first_id": "msg_67e8ff7445408191af5d6f4a87a9d3fe09a3a922c4f4221b",
          "last_id": "msg_67e8ff7258a081919e7964ac7b344bc909a3a922c4f4221b",
          "has_more": false
        }
        
        """;
    #endregion
}

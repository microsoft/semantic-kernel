// Copyright (c) Microsoft. All rights reserved.
using Azure.AI.Agents.Persistent;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted.AzureAgents;

/// <summary>
/// Demonstrate parsing JSON response.
/// </summary>
public class Step10_JsonResponse(ITestOutputHelper output) : BaseAzureAgentTest(output)
{
    private const string TutorInstructions =
        """
        Think step-by-step and rate the user input on creativity and expressiveness from 1-100.

        Respond in JSON format with the following JSON schema:

        {
            "score": "integer (1-100)",
            "notes": "the reason for your score"
        }
        """;

    [Fact]
    public async Task UseJsonObjectResponse()
    {
        PersistentAgent definition =
            await this.Client.Administration.CreateAgentAsync(
                TestConfiguration.AzureAI.ChatModelId,
                instructions: TutorInstructions,
                responseFormat:
                    BinaryData.FromString(
                        """
                        {
                            "type": "json_object"
                        }                        
                        """));

        AzureAIAgent agent = new(definition, this.Client);

        await ExecuteAgent(agent);
    }

    [Fact]
    public async Task UseJsonSchemaResponse()
    {
        PersistentAgent definition =
            await this.Client.Administration.CreateAgentAsync(
                TestConfiguration.AzureAI.ChatModelId,
                instructions: TutorInstructions,
                responseFormat: BinaryData.FromString(
                    """
                    {
                        "type": "json_schema",
                        "json_schema":
                        {
                          "type": "object",
                          "name": "scoring",
                          "schema": {
                              "type": "object",
                              "properties": {
                                  "score": {
                                      "type": "number"
                                  },
                                  "notes": {
                                      "type": "string"
                                  }
                              },
                              "required": [
                                  "score",
                                  "notes"
                              ],
                              "additionalProperties": false
                          },
                          "strict": true
                      }
                    }
                    """));

        AzureAIAgent agent = new(definition, this.Client);

        await ExecuteAgent(agent);
    }

    private async Task ExecuteAgent(AzureAIAgent agent)
    {
        AzureAIAgentThread thread = new(agent.Client);

        await InvokeAgentAsync("The sunset is very colorful.");
        await InvokeAgentAsync("The sunset is setting over the mountains.");
        await InvokeAgentAsync("The sunset is setting over the mountains and filled the sky with a deep red flame, setting the clouds ablaze.");

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            ChatMessageContent message = new(AuthorRole.User, input);
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in agent.InvokeAsync(message, thread))
            {
                this.WriteAgentChatMessage(response);
            }
        }
    }
}

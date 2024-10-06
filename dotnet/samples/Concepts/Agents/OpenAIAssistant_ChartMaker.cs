// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Files;

namespace Agents;

/// <summary>
/// Demonstrate using code-interpreter with <see cref="OpenAIAssistantAgent"/> to
/// produce image content displays the requested charts.
/// </summary>
public class OpenAIAssistant_ChartMaker(ITestOutputHelper output) : BaseAgentsTest(output)
{
    private const string AgentName = "ChartMaker";
    private const string AgentInstructions = "Create charts as requested without explanation.";

    [Fact]
    public async Task GenerateChartWithOpenAIAssistantAgentAsync()
    {
        OpenAIClientProvider provider = this.GetClientProvider();

<<<<<<< Updated upstream
<<<<<<< Updated upstream
        FileClient fileClient = provider.Client.GetFileClient();
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        FileClient fileClient = provider.Client.GetFileClient();
=======
        OpenAIFileClient fileClient = provider.Client.GetOpenAIFileClient();
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

        // Define the agent
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                kernel: new(),
                provider,
                new(this.Model)
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
                kernel: new(),
                provider,
                new(this.Model)
=======
                provider,
                definition: new OpenAIAssistantDefinition(this.Model)
                kernel: new(),
                provider,
                new(this.Model)
                provider,
                definition: new OpenAIAssistantDefinition(this.Model)
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                {
                    Instructions = AgentInstructions,
                    Name = AgentName,
                    EnableCodeInterpreter = true,
                    Metadata = AssistantSampleMetadata,
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                });
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
                });
=======
                },
                kernel: new());
                });
                },
                kernel: new());
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

        // Create a chat for agent interaction.
        AgentGroupChat chat = new();

        // Respond to user input
        try
        {
            await InvokeAgentAsync(
                """
                Display this data using a bar-chart:

                Banding  Brown Pink Yellow  Sum
                X00000   339   433     126  898
                X00300    48   421     222  691
                X12345    16   395     352  763
                Others    23   373     156  552
                Sum      426  1622     856 2904
                """);

            await InvokeAgentAsync("Can you regenerate this same chart using the category names as the bar colors?");
            await InvokeAgentAsync("Perfect, can you regenerate this as a line chart?");
        }
        finally
        {
            await agent.DeleteAsync();
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
<<<<<<< main
            chat.Add(new ChatMessageContent(AuthorRole.User, input));

            Console.WriteLine($"# {AuthorRole.User}: '{input}'");
=======
>>>>>>> upstream/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
            chat.Add(new ChatMessageContent(AuthorRole.User, input));

            Console.WriteLine($"# {AuthorRole.User}: '{input}'");
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            ChatMessageContent message = new(AuthorRole.User, input);
            chat.AddChatMessage(new(AuthorRole.User, input));
            this.WriteAgentChatMessage(message);

            await foreach (ChatMessageContent response in chat.InvokeAsync(agent))
            {
                this.WriteAgentChatMessage(response);
                await this.DownloadResponseImageAsync(fileClient, response);
            }
        }
    }
}

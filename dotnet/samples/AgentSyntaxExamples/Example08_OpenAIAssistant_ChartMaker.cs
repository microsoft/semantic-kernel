// Copyright (c) Microsoft. All rights reserved.
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// Demonstrate creation of <see cref="ChatCompletionAgent"/> and
/// eliciting its response to three explicit user messages.
/// </summary>
public class Example08_OpenAIAssistant_ChartMaker : BaseTest
{
    private const string AgentName = "ChartMaker";
    private const string AgentInstructions = "Create charts as requested without explanation.";

    [Fact]
    public async Task RunAsync()
    {
        // Define the agent
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                kernel: this.CreateEmptyKernel(),
                config: new(this.GetApiKey(), this.GetEndpoint()),
                new()
                {
                    Model = this.GetModel(),
                    Instructions = AgentInstructions,
                    Name = AgentName,
                    EnableCodeInterpreter = true,
                });

        // Create a chat for agent interaction.
        var chat = new AgentGroupChat();

        // Respond to user input
        try
        {
            await WriteAgentResponseAsync(@"
                Display this data using a bar-chart:

                Banding  Brown Pink Yellow  Sum
                X00000   339   433     126  898
                X00300    48   421     222  691
                X12345    16   395     352  763
                Others    23   373     156  552
                Sum      426  1622     856 2904");

            await WriteAgentResponseAsync("Can you regenerate this same chart using the category names as the bar colors?");
        }
        finally
        {
            await agent.DeleteAsync();
        }

        // Local function to invoke agent and display the conversation messages.
        async Task WriteAgentResponseAsync(string input)
        {
            chat.AddUserMessage(input);
            this.WriteLine($"# {AuthorRole.User}: '{input}'");

            await foreach (var content in chat.InvokeAsync(agent))
            {
                this.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
            }
        }
    }

    public Example08_OpenAIAssistant_ChartMaker(ITestOutputHelper output)
        : base(output)
    { }
}

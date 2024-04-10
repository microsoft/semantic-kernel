// Copyright (c) Microsoft. All rights reserved.
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// Demonstrate using code-interpreter with <see cref="OpenAIAssistantAgent"/> to
/// produce image content displays the requested charts.
/// </summary>
public class Example08_OpenAIAssistant_ChartMaker : BaseTest
{
    /// <summary>
    /// Target Open AI services.
    /// </summary>
    protected override bool ForceOpenAI => true;

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
                    Instructions = AgentInstructions,
                    Name = AgentName,
                    EnableCodeInterpreter = true,
                    Model = this.GetModel(),
                });

        // Create a chat for agent interaction.
        var chat = new AgentGroupChat();

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
        }
        finally
        {
            await agent.DeleteAsync();
        }

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, input));

            this.WriteLine($"# {AuthorRole.User}: '{input}'");

            await foreach (var message in chat.InvokeAsync(agent))
            {
                if (!string.IsNullOrWhiteSpace(message.Content))
                {
                    this.WriteLine($"# {message.Role} - {message.AuthorName ?? "*"}: '{message.Content}'");
                }

                foreach (var fileReference in message.Items.OfType<FileReferenceContent>())
                {
                    this.WriteLine($"# {message.Role} - {message.AuthorName ?? "*"}: #{fileReference.FileId}");
                }
            }
        }
    }

    public Example08_OpenAIAssistant_ChartMaker(ITestOutputHelper output)
        : base(output)
    { }
}

// Copyright (c) Microsoft. All rights reserved.
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// Demonstrate creation of <see cref="ChatCompletionAgent"/> and
/// eliciting its response to three explicit user messages.
/// </summary>
public class Example05_OpenAIAssistant_Plugins : BaseTest
{
    /// <inheritdoc/>
    protected override bool ForceOpenAI => true; // $$$

    private const string ParrotName = "Parrot";
    private const string ParrotInstructions = "Repeat the user message in the voice of a pirate and then end with a parrot sound.";

    [Fact]
    public async Task RunAsync()
    {
        // Define the agent
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                kernel: this.CreateKernelWithChatCompletion(),
                apiKey: this.GetApiKey(),
                new()
                {
                    Instructions = ParrotInstructions,
                    Name = ParrotName,
                    Model = this.GetModel(),
                });

        // Create a chat for agent interaction.
        var chat = new AgentGroupChat();

        // Respond to user input
        try
        {
            await WriteAgentResponseAsync("Fortune favors the bold.");
            await WriteAgentResponseAsync("I came, I saw, I conquered.");
            await WriteAgentResponseAsync("Practice makes perfect.");
        }
        finally
        {
            //await OpenAIAssistantAgent.DeleteAsync(agent.Id); $$$
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

    public Example05_OpenAIAssistant_Plugins(ITestOutputHelper output)
        : base(output)
    { }
}

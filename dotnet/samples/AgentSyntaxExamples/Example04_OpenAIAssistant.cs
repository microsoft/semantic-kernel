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
public class Example04_OpenAIAssistant : BaseTest
{
    private const string ParrotName = "Parrot";
    private const string ParrotInstructions = "Repeat the user message in the voice of a pirate and then end with a parrot sound.";

    [Fact]
    public async Task RunAsync()
    {
        // Define the agent
        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                kernel: this.CreateEmptyKernel(),
                config: new(this.GetApiKey(), this.GetEndpoint()),
                definition: new()
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

    public Example04_OpenAIAssistant(ITestOutputHelper output)
        : base(output)
    { }
}

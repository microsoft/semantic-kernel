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
public class Example06_OpenAIAssistant_CodeInterpreter : BaseTest
{
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
                    EnableCodeInterpreter = true,
                });

        // Create a chat for agent interaction.
        var chat = new AgentGroupChat();

        // Respond to user input
        try
        {
            await WriteAgentResponseAsync("What is the solution to `3x + 2 = 14`?");
            await WriteAgentResponseAsync("What is the fibinacci sequence until 101?");
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

    public Example06_OpenAIAssistant_CodeInterpreter(ITestOutputHelper output)
        : base(output)
    { }
}

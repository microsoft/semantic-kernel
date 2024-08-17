// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.ChatCompletion;
using Resources;

namespace GettingStarted;

/// <summary>
/// Demonstrate parsing JSON response.
/// </summary>
public class Step5_JsonResult(ITestOutputHelper output) : BaseTest(output)
{
    private const int ScoreCompletionThreshold = 70;

    private const string TutorName = "Tutor";
    private const string TutorInstructions =
        """
        Think step-by-step and rate the user input on creativity and expressivness from 1-100.

        Respond in JSON format with the following JSON schema:

        {
            "score": "integer (1-100)",
            "notes": "the reason for your score"
        }
        """;

    [Fact]
    public async Task RunAsync()
    {
        // Define the agents
        ChatCompletionAgent agent =
            new()
            {
                Instructions = TutorInstructions,
                Name = TutorName,
                Kernel = this.CreateKernelWithChatCompletion(),
            };

        // Create a chat for agent interaction.
        AgentGroupChat chat =
            new()
            {
                ExecutionSettings =
                    new()
                    {
                        // Here a TerminationStrategy subclass is used that will terminate when
                        // the response includes a score that is greater than or equal to 70.
                        TerminationStrategy = new ThresholdTerminationStrategy()
                    }
            };

        // Respond to user input
        await InvokeAgentAsync("The sunset is very colorful.");
        await InvokeAgentAsync("The sunset is setting over the mountains.");
        await InvokeAgentAsync("The sunset is setting over the mountains and filled the sky with a deep red flame, setting the clouds ablaze.");

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(string input)
        {
            chat.Add(new ChatMessageContent(AuthorRole.User, input));

            Console.WriteLine($"# {AuthorRole.User}: '{input}'");

            await foreach (var content in chat.InvokeAsync(agent))
            {
                Console.WriteLine($"# {content.Role} - {content.AuthorName ?? "*"}: '{content.Content}'");
                Console.WriteLine($"# IS COMPLETE: {chat.IsComplete}");
            }
        }
    }

    private record struct InputScore(int score, string notes);

    private sealed class ThresholdTerminationStrategy : TerminationStrategy
    {
        protected override Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken)
        {
            string lastMessageContent = history[history.Count - 1].Content ?? string.Empty;

            InputScore? result = JsonResultTranslator.Translate<InputScore>(lastMessageContent);

            return Task.FromResult((result?.score ?? 0) >= ScoreCompletionThreshold);
        }
    }
}

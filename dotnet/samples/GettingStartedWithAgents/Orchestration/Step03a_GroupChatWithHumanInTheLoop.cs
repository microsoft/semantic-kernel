// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrates how to use the <see cref="GroupChatOrchestration"/> with human in the loop
/// </summary>
public class Step03a_GroupChatWithHumanInTheLoop(ITestOutputHelper output) : BaseOrchestrationTest(output)
{
    [Fact]
    public async Task GroupChatWithHumanAsync()
    {
        // Define the agents
        ChatCompletionAgent writer =
            this.CreateAgent(
                name: "CopyWriter",
                description: "A copy writer",
                instructions:
                """
                You are a copywriter with ten years of experience and are known for brevity and a dry humor.
                The goal is to refine and decide on the single best copy as an expert in the field.
                Only provide a single proposal per response.
                You're laser focused on the goal at hand.
                Don't waste time with chit chat.
                Consider suggestions when refining an idea.
                """);
        ChatCompletionAgent editor =
            this.CreateAgent(
                name: "Reviewer",
                description: "An editor.",
                instructions:
                """
                You are an art director who has opinions about copywriting born of a love for David Ogilvy.
                The goal is to determine if the given copy is acceptable to print.
                If so, state that it is approved.
                If not, provide insight on how to refine suggested copy without example.
                """);

        // Create a monitor to capturing agent responses (via ResponseCallback)
        // to display at the end of this sample. (optional)
        // NOTE: Create your own callback to capture responses in your application or service.
        OrchestrationMonitor monitor = new();

        // Define the orchestration
        GroupChatOrchestration orchestration =
            new(
                new CustomRoundRobinGroupChatManager()
                {
                    MaximumInvocationCount = 5,
                    InteractiveCallback = () =>
                    {
                        ChatMessageContent input = new(AuthorRole.User, "I like it");
                        Console.WriteLine($"\n# INPUT: {input.Content}\n");
                        return ValueTask.FromResult(input);
                    }
                },
                writer,
                editor)
            {
                LoggerFactory = this.LoggerFactory,
                ResponseCallback = monitor.ResponseCallback,
            };

        // Start the runtime
        InProcessRuntime runtime = new();
        await runtime.StartAsync();

        // Run the orchestration
        string input = "Create a slogon for a new eletric SUV that is affordable and fun to drive.";
        Console.WriteLine($"\n# INPUT: {input}\n");
        OrchestrationResult<string> result = await orchestration.InvokeAsync(input, runtime);
        string text = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds * 3));
        Console.WriteLine($"\n# RESULT: {text}");

        await runtime.RunUntilIdleAsync();
    }

    /// <summary>
    /// Define a custom group chat manager that enables user input.
    /// </summary>
    /// <remarks>
    /// User input is achieved by overriding the default round robin manager
    /// to allow user input after the reviewer agent's message.
    /// </remarks>
    private sealed class CustomRoundRobinGroupChatManager : RoundRobinGroupChatManager
    {
        public override ValueTask<GroupChatManagerResult<bool>> ShouldRequestUserInput(ChatHistory history, CancellationToken cancellationToken = default)
        {
            string? lastAgent = history.LastOrDefault()?.AuthorName;

            if (lastAgent is null)
            {
                return ValueTask.FromResult(new GroupChatManagerResult<bool>(false) { Reason = "No agents have spoken yet." });
            }

            if (lastAgent == "Reviewer")
            {
                return ValueTask.FromResult(new GroupChatManagerResult<bool>(true) { Reason = "User input is needed after the reviewer's message." });
            }

            return ValueTask.FromResult(new GroupChatManagerResult<bool>(false) { Reason = "User input is not needed until the reviewer's message." });
        }
    }
}

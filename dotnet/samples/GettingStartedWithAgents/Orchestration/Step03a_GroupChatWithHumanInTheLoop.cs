// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit.Sdk;
using YamlDotNet.Core;

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
            this.CreateChatCompletionAgent(
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
            this.CreateChatCompletionAgent(
                name: "Reviewer",
                description: "An editor.",
                instructions:
                """
                You are an art director who has opinions about copywriting born of a love for David Ogilvy.
                The goal is to determine if the given copy is acceptable to print.
                If so, state: "I Approve".
                If not, provide insight on how to refine suggested copy without example.
                """);

        // Create a monitor to capturing agent responses (via ResponseCallback)
        // to display at the end of this sample. (optional)
        // NOTE: Create your own callback to capture responses in your application or service.
        OrchestrationMonitor monitor = new();

        // Define the orchestration
        bool didUserRespond = false;
        GroupChatOrchestration orchestration =
            new(
                new HumanInTheLoopChatManager(writer.Name!, editor.Name!)
                {
                    MaximumInvocationCount = 5,
                    InteractiveCallback = () =>
                    {
                        // Simlulate user input that first replies "No" and then "Yes"
                        ChatMessageContent input = new(AuthorRole.User, didUserRespond ? "Yes" : "More pizzazz");
                        didUserRespond = true;
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
        string input = "Create a slogan for a new electric SUV that is affordable and fun to drive.";
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
    private sealed class HumanInTheLoopChatManager(string authorName, string criticName) : RoundRobinGroupChatManager
    {
        public override ValueTask<GroupChatManagerResult<string>> FilterResults(ChatHistory history, CancellationToken cancellationToken = default)
        {
            ChatMessageContent finalResult = history.Last(message => message.AuthorName == authorName);
            return ValueTask.FromResult(new GroupChatManagerResult<string>($"{finalResult}") { Reason = "The approved copy." });
        }

        /// <inheritdoc/>
        public override async ValueTask<GroupChatManagerResult<bool>> ShouldTerminate(ChatHistory history, CancellationToken cancellationToken = default)
        {
            // Has the maximum invocation count been reached?
            GroupChatManagerResult<bool> result = await base.ShouldTerminate(history, cancellationToken);
            if (!result.Value)
            {
                // If not, check if the reviewer has approved the copy.
                ChatMessageContent? lastMessage = history.LastOrDefault();
                if (lastMessage is not null && lastMessage.Role == AuthorRole.User && $"{lastMessage}".Contains("Yes", StringComparison.OrdinalIgnoreCase))
                {
                    // If the reviewer approves, we terminate the chat.
                    result = new GroupChatManagerResult<bool>(true) { Reason = "The user is satisfied with the copy." };
                }
            }
            return result;
        }

        public override ValueTask<GroupChatManagerResult<bool>> ShouldRequestUserInput(ChatHistory history, CancellationToken cancellationToken = default)
        {
            ChatMessageContent? lastMessage = history.LastOrDefault();

            if (lastMessage is null)
            {
                return ValueTask.FromResult(new GroupChatManagerResult<bool>(false) { Reason = "No agents have spoken yet." });
            }

            if (lastMessage is not null && lastMessage.AuthorName == criticName && $"{lastMessage}".Contains("I Approve", StringComparison.OrdinalIgnoreCase))
            {
                return ValueTask.FromResult(new GroupChatManagerResult<bool>(true) { Reason = "User input is needed after the reviewer's message." });
            }

            return ValueTask.FromResult(new GroupChatManagerResult<bool>(false) { Reason = "User input is not needed until the reviewer's message." });
        }
    }
}

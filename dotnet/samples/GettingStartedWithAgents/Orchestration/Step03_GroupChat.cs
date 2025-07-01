// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrates how to use the <see cref="GroupChatOrchestration"/> ith a default
/// round robin manager for controlling the flow of conversation in a round robin fashion.
/// </summary>
/// <remarks>
/// Think of the group chat manager as a state machine, with the following possible states:
/// - Request for user message
/// - Termination, after which the manager will try to filter a result from the conversation
/// - Continuation, at which the manager will select the next agent to speak.
/// </remarks>
public class Step03_GroupChat(ITestOutputHelper output) : BaseOrchestrationTest(output)
{
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task GroupChatAsync(bool streamedResponse)
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
            new(new RoundRobinGroupChatManager()
            {
                MaximumInvocationCount = 5
            },
            writer,
            editor)
            {
                LoggerFactory = this.LoggerFactory,
                ResponseCallback = monitor.ResponseCallback,
                StreamingResponseCallback = streamedResponse ? monitor.StreamingResultCallback : null,
            };

        // Start the runtime
        InProcessRuntime runtime = new();
        await runtime.StartAsync();

        string input = "Create a slogon for a new eletric SUV that is affordable and fun to drive.";
        Console.WriteLine($"\n# INPUT: {input}\n");
        OrchestrationResult<string> result = await orchestration.InvokeAsync(input, runtime);
        string text = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds * 3));
        Console.WriteLine($"\n# RESULT: {text}");

        await runtime.RunUntilIdleAsync();

        Console.WriteLine("\n\nORCHESTRATION HISTORY");
        foreach (ChatMessageContent message in monitor.History)
        {
            this.WriteAgentChatMessage(message);
        }
    }
}

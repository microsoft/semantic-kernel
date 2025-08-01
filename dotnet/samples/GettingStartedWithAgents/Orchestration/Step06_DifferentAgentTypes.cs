// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Magentic;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Concurrent;
using Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;
using Microsoft.SemanticKernel.Agents.Orchestration.Handoff;
using Microsoft.SemanticKernel.Agents.Orchestration.Sequential;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrates how to use the <see cref="MagenticOrchestration"/> with two agents:
/// - A Research agent that can perform web searches
/// - A Coder agent that can run code using the code interpreter
/// </summary>
public class Step06_DifferentAgentTypes(ITestOutputHelper output) : BaseOrchestrationTest(output)
{
    [Fact]
    public async Task ConcurrentOrchestrationAsync()
    {
        // Define the agents
        Agent physicist =
            this.CreateChatCompletionAgent(
                instructions: "You are an expert in physics. You answer questions from a physics perspective.",
                name: "Physicist",
                description: "An expert in physics");
        Agent chemist =
            await this.CreateAzureAIAgentAsync(
                instructions: "You are an expert in chemistry. You answer questions from a chemistry perspective.",
                name: "Chemist",
                description: "An expert in chemistry");

        // Create a monitor to capturing agent responses (via ResponseCallback)
        // to display at the end of this sample. (optional)
        // NOTE: Create your own callback to capture responses in your application or service.
        OrchestrationMonitor monitor = new();

        // Define the orchestration
        ConcurrentOrchestration orchestration =
            new(physicist, chemist)
            {
                LoggerFactory = this.LoggerFactory,
                ResponseCallback = monitor.ResponseCallback,
            };

        // Start the runtime
        InProcessRuntime runtime = new();
        await runtime.StartAsync();

        // Run the orchestration
        string input = "What is temperature?";
        Console.WriteLine($"\n# INPUT: {input}\n");
        OrchestrationResult<string[]> result = await orchestration.InvokeAsync(input, runtime);

        string[] output = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds));
        Console.WriteLine($"\n# RESULT:\n{string.Join("\n\n", output.Select(text => $"{text}"))}");

        await runtime.RunUntilIdleAsync();

        Console.WriteLine("\n\nORCHESTRATION HISTORY");
        foreach (ChatMessageContent message in monitor.History)
        {
            this.WriteAgentChatMessage(message);
        }
    }

    [Fact]
    public async Task SequentialOrchestrationAsync()
    {
        // Define the agents
        Agent analystAgent =
            this.CreateChatCompletionAgent(
                name: "Analyst",
                instructions:
                """
                You are a marketing analyst. Given a product description, identify:
                - Key features
                - Target audience
                - Unique selling points
                """,
                description: "A agent that extracts key concepts from a product description.");
        Agent writerAgent =
            await this.CreateOpenAIAssistantAgentAsync(
                name: "copywriter",
                instructions:
                """
                You are a marketing copywriter. Given a block of text describing features, audience, and USPs,
                compose a compelling marketing copy (like a newsletter section) that highlights these points.
                Output should be short (around 150 words), output just the copy as a single text block.
                """,
                description: "An agent that writes a marketing copy based on the extracted concepts.");
        Agent editorAgent =
            await this.CreateAzureAIAgentAsync(
                name: "editor",
                instructions:
                """
                You are an editor. Given the draft copy, correct grammar, improve clarity, ensure consistent tone,
                give format and make it polished. Output the final improved copy as a single text block.
                """,
                description: "An agent that formats and proofreads the marketing copy.");

        // Create a monitor to capturing agent responses (via ResponseCallback)
        // to display at the end of this sample. (optional)
        // NOTE: Create your own callback to capture responses in your application or service.
        OrchestrationMonitor monitor = new();
        // Define the orchestration
        SequentialOrchestration orchestration =
            new(analystAgent, writerAgent, editorAgent)
            {
                LoggerFactory = this.LoggerFactory,
                ResponseCallback = monitor.ResponseCallback,
            };

        // Start the runtime
        InProcessRuntime runtime = new();
        await runtime.StartAsync();

        // Run the orchestration
        string input = "An eco-friendly stainless steel water bottle that keeps drinks cold for 24 hours";
        Console.WriteLine($"\n# INPUT: {input}\n");
        OrchestrationResult<string> result = await orchestration.InvokeAsync(input, runtime);
        string text = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds * 2));
        Console.WriteLine($"\n# RESULT: {text}");

        await runtime.RunUntilIdleAsync();

        Console.WriteLine("\n\nORCHESTRATION HISTORY");
        foreach (ChatMessageContent message in monitor.History)
        {
            this.WriteAgentChatMessage(message);
        }
    }

    [Fact]
    public async Task GroupChatOrchestrationAsync()
    {
        // Define the agents
        Agent writer =
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
        Agent editor =
            await this.CreateOpenAIAssistantAgentAsync(
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
        GroupChatOrchestration orchestration =
            new(new AuthorCriticManager(writer.Name!, editor.Name!)
            {
                MaximumInvocationCount = 5
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

        string input = "Create a slogan for a new electric SUV that is affordable and fun to drive.";
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

    [Fact]
    public async Task HandoffOrchestrationAsync()
    {
        // Define the agents & tools
        Agent triageAgent =
            this.CreateChatCompletionAgent(
                instructions: "A customer support agent that triages issues.",
                name: "TriageAgent",
                description: "Handle customer requests.");
        Agent statusAgent =
            this.CreateChatCompletionAgent(
                name: "OrderStatusAgent",
                instructions: "Handle order status requests.",
                description: "A customer support agent that checks order status.");
        statusAgent.Kernel.Plugins.Add(KernelPluginFactory.CreateFromObject(new OrderStatusPlugin()));
        Agent returnAgent =
            this.CreateChatCompletionAgent(
                name: "OrderReturnAgent",
                instructions: "Handle order return requests.",
                description: "A customer support agent that handles order returns.");
        returnAgent.Kernel.Plugins.Add(KernelPluginFactory.CreateFromObject(new OrderReturnPlugin()));
        Agent refundAgent =
            this.CreateChatCompletionAgent(
                name: "OrderRefundAgent",
                instructions: "Handle order refund requests.",
                description: "A customer support agent that handles order refund.");
        refundAgent.Kernel.Plugins.Add(KernelPluginFactory.CreateFromObject(new OrderRefundPlugin()));

        // Create a monitor to capturing agent responses (via ResponseCallback)
        // to display at the end of this sample. (optional)
        // NOTE: Create your own callback to capture responses in your application or service.
        OrchestrationMonitor monitor = new();
        // Define user responses for InteractiveCallback (since sample is not interactive)
        Queue<string> responses = new();
        string task = "I am a customer that needs help with my orders";
        responses.Enqueue("I'd like to track the status of my order");
        responses.Enqueue("My order ID is 123");
        responses.Enqueue("I want to return another order of mine");
        responses.Enqueue("Order ID 321");
        responses.Enqueue("Broken item");
        responses.Enqueue("No, bye");
        // Define the orchestration
        HandoffOrchestration orchestration =
            new(OrchestrationHandoffs
                    .StartWith(triageAgent)
                    .Add(triageAgent, statusAgent, returnAgent, refundAgent)
                    .Add(statusAgent, triageAgent, "Transfer to this agent if the issue is not status related")
                    .Add(returnAgent, triageAgent, "Transfer to this agent if the issue is not return related")
                    .Add(refundAgent, triageAgent, "Transfer to this agent if the issue is not refund related"),
                triageAgent,
                statusAgent,
                returnAgent,
                refundAgent)
            {
                InteractiveCallback = () =>
                {
                    string input = responses.Dequeue();
                    Console.WriteLine($"\n# INPUT: {input}\n");
                    return ValueTask.FromResult(new ChatMessageContent(AuthorRole.User, input));
                },
                LoggerFactory = this.LoggerFactory,
                ResponseCallback = monitor.ResponseCallback,
            };

        // Start the runtime
        InProcessRuntime runtime = new();
        await runtime.StartAsync();

        // Run the orchestration
        Console.WriteLine($"\n# INPUT:\n{task}\n");
        OrchestrationResult<string> result = await orchestration.InvokeAsync(task, runtime);

        string text = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds * 10));
        Console.WriteLine($"\n# RESULT: {text}");

        await runtime.RunUntilIdleAsync();

        Console.WriteLine("\n\nORCHESTRATION HISTORY");
        foreach (ChatMessageContent message in monitor.History)
        {
            this.WriteAgentChatMessage(message);
        }
    }

    private sealed class OrderStatusPlugin
    {
        [KernelFunction]
        public string CheckOrderStatus(string orderId) => $"Order {orderId} is shipped and will arrive in 2-3 days.";
    }

    private sealed class OrderReturnPlugin
    {
        [KernelFunction]
        public string ProcessReturn(string orderId, string reason) => $"Return for order {orderId} has been processed successfully.";
    }

    private sealed class OrderRefundPlugin
    {
        [KernelFunction]
        public string ProcessReturn(string orderId, string reason) => $"Refund for order {orderId} has been processed successfully.";
    }

    private sealed class AuthorCriticManager(string authorName, string criticName) : RoundRobinGroupChatManager
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
                if (lastMessage is not null && lastMessage.AuthorName == criticName && $"{lastMessage}".Contains("I Approve", StringComparison.OrdinalIgnoreCase))
                {
                    // If the reviewer approves, we terminate the chat.
                    result = new GroupChatManagerResult<bool>(true) { Reason = "The reviewer has approved the copy." };
                }
            }
            return result;
        }
    }
}

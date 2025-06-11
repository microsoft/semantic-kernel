// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Handoff;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrates how to use the <see cref="HandoffOrchestration"/> that represents
/// a customer support triage system.The orchestration consists of 4 agents, each specialized
/// in a different area of customer support: triage, refunds, order status, and order returns.
/// </summary>
public class Step04_Handoff(ITestOutputHelper output) : BaseOrchestrationTest(output)
{
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task OrderSupportAsync(bool streamedResponse)
    {
        // Define the agents & tools
        ChatCompletionAgent triageAgent =
            this.CreateAgent(
                instructions: "A customer support agent that triages issues.",
                name: "TriageAgent",
                description: "Handle customer requests.");
        ChatCompletionAgent statusAgent =
            this.CreateAgent(
                name: "OrderStatusAgent",
                instructions: "Handle order status requests.",
                description: "A customer support agent that checks order status.");
        statusAgent.Kernel.Plugins.Add(KernelPluginFactory.CreateFromObject(new OrderStatusPlugin()));
        ChatCompletionAgent returnAgent =
            this.CreateAgent(
                name: "OrderReturnAgent",
                instructions: "Handle order return requests.",
                description: "A customer support agent that handles order returns.");
        returnAgent.Kernel.Plugins.Add(KernelPluginFactory.CreateFromObject(new OrderReturnPlugin()));
        ChatCompletionAgent refundAgent =
            this.CreateAgent(
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
                StreamingResponseCallback = streamedResponse ? monitor.StreamingResultCallback : null,
            };

        // Start the runtime
        InProcessRuntime runtime = new();
        await runtime.StartAsync();

        // Run the orchestration
        Console.WriteLine($"\n# INPUT:\n{task}\n");
        OrchestrationResult<string> result = await orchestration.InvokeAsync(task, runtime);

        string text = await result.GetValueAsync(TimeSpan.FromSeconds(300));
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
}

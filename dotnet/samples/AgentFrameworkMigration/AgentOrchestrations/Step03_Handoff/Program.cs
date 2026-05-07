// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Text.Json;
using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Agents.AI;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Handoff;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;
using Microsoft.SemanticKernel.ChatCompletion;

var endpoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT") ?? throw new InvalidOperationException("AZURE_OPENAI_ENDPOINT is not set.");
var deploymentName = Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT_NAME") ?? "gpt-4o-mini";

// Queries to simulate user input during the interactive orchestration
List<string> Queries = [
    "I'd like to track the status of my first order 123.",
    "I want to return another order of mine whose ID is 456 because it arrived damaged.",
];

// This sample compares running handoff orchestrations using
// Semantic Kernel and the Agent Framework.
Console.WriteLine("=== Semantic Kernel Handoff Orchestration ===");
// State to help format the streaming output
bool newAgentTurn = true;
string previousFunctionCallId = string.Empty;
await SKHandoffOrchestration();

Console.WriteLine("\n=== Agent Framework Handoff Agent Workflow ===");
await AFHandoffAgentWorkflow();

# region SKHandoffOrchestration
[KernelFunction]
string SKCheckOrderStatus(string orderId) => $"Order {orderId} is shipped and will arrive in 2-3 days.";

[KernelFunction]
string SKProcessReturn(string orderId, string reason) => $"Return for order {orderId} has been processed successfully.";

[KernelFunction]
string SKProcessRefund(string orderId, string reason) => $"Refund for order {orderId} has been processed successfully.";

#pragma warning disable SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
async Task SKHandoffOrchestration()
{
    // Create agents
    var triageAgent = GetSKAgent(
        instructions: "You are a customer support agent that triages issues.",
        name: "TriageAgent",
        description: "Handle customer requests.");
    var statusAgent = GetSKAgent(
        instructions: "You are a customer support agent that checks order status.",
        name: "OrderStatusAgent",
        description: "Handle order status requests.");
    statusAgent.Kernel.Plugins.AddFromFunctions("OrderStatusPlugin", [KernelFunctionFactory.CreateFromMethod(SKCheckOrderStatus)]);
    var returnAgent = GetSKAgent(
        instructions: "You are a customer support agent that handles order returns.",
        name: "OrderReturnAgent",
        description: "Handle order return requests.");
    returnAgent.Kernel.Plugins.AddFromFunctions("OrderReturnPlugin", [KernelFunctionFactory.CreateFromMethod(SKProcessReturn)]);
    var refundAgent = GetSKAgent(
        instructions: "You are a customer support agent that handles order refunds.",
        name: "OrderRefundAgent",
        description: "Handle order refund requests.");
    refundAgent.Kernel.Plugins.AddFromFunctions("OrderRefundPlugin", [KernelFunctionFactory.CreateFromMethod(SKProcessRefund)]);

    Queue<string> queries = new(Queries);

    // Create orchestration with handoffs
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
                string input = queries.Count > 0 ? queries.Dequeue() : "exit";
                Console.WriteLine($"\nUser: {input}");
                return ValueTask.FromResult(new ChatMessageContent(AuthorRole.User, input));
            },
            StreamingResponseCallback = StreamingResultCallback,
        };

    InProcessRuntime runtime = new();
    await runtime.StartAsync();

    // Run the orchestration
    OrchestrationResult<string> result = await orchestration.InvokeAsync(
        "I am a customer that needs help with my two orders",
        runtime);
    string text = await result.GetValueAsync();
    Console.WriteLine($"\nFinal Result: {text}");

    await runtime.RunUntilIdleAsync();
}
#pragma warning restore SKEXP0110 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

ChatCompletionAgent GetSKAgent(string instructions, string name, string description)
{
    var kernel = Kernel.CreateBuilder().AddAzureOpenAIChatCompletion(deploymentName, endpoint, new AzureCliCredential()).Build();
    return new ChatCompletionAgent()
    {
        Kernel = kernel,
        Instructions = instructions,
        Description = description,
        Name = name
    };
}

ValueTask StreamingResultCallback(StreamingChatMessageContent streamedResponse, bool isFinal)
{
    if (newAgentTurn)
    {
        Console.Write($"\n{streamedResponse.AuthorName}: ");
        newAgentTurn = false;
    }
    Console.Write(streamedResponse.Content);

    if (streamedResponse.Items.OfType<StreamingFunctionCallUpdateContent>().FirstOrDefault()
            is StreamingFunctionCallUpdateContent call)
    {
        if (call.CallId is not null && previousFunctionCallId != call.CallId)
        {
            Console.Write($"\nCalling function '{call.Name}' with arguments: ");
            previousFunctionCallId = call.CallId;
        }
        if (!string.IsNullOrEmpty(call.Arguments))
        {
            Console.Write($"{call.Arguments}");
        }
    }

    if (isFinal)
    {
        newAgentTurn = true;
        previousFunctionCallId = string.Empty;
        Console.WriteLine();
    }

    return ValueTask.CompletedTask;
}
# endregion

# region AFHandoffAgentWorkflow
[Description("Get the order status for a given order ID.")]
static string AFCheckOrderStatus([Description("The order ID to check the status for.")] string orderId)
    => $"Order {orderId} is shipped and will arrive in 2-3 days.";

[Description("Process a return for a given order ID.")]
static string AFProcessReturn(
    [Description("The order ID to process the return for.")] string orderId,
    [Description("The reason for the return.")] string reason)
    => $"Return for order {orderId} has been processed successfully for the following reason: {reason}.";

[Description("Process a refund for a given order ID.")]
static string AFProcessRefund([Description("The order ID to process the refund for.")] string orderId)
    => $"Refund for order {orderId} has been processed successfully.";

async Task AFHandoffAgentWorkflow()
{
    // Create agents
    var client = new AzureOpenAIClient(new Uri(endpoint), new AzureCliCredential()).GetChatClient(deploymentName).AsIChatClient();

    ChatClientAgent triageAgent = new(client,
        instructions: "A customer support agent that triages issues.",
        name: "TriageAgent",
        description: "Handle customer requests.");
    ChatClientAgent statusAgent = new(client,
        name: "OrderStatusAgent",
        instructions: "Handle order status requests.",
        description: "A customer support agent that checks order status.",
        tools: [AIFunctionFactory.Create(AFCheckOrderStatus)]);
    ChatClientAgent returnAgent = new(client,
        name: "OrderReturnAgent",
        instructions: "Handle order return requests.",
        description: "A customer support agent that handles order returns.",
        tools: [AIFunctionFactory.Create(AFProcessReturn)]);
    ChatClientAgent refundAgent = new(client,
        name: "OrderRefundAgent",
        instructions: "Handle order refund requests.",
        description: "A customer support agent that handles order refund.",
        tools: [AIFunctionFactory.Create(AFProcessRefund)]);

    // Create workflow with handoffs
    var handoffAgentWorkflow = AgentWorkflowBuilder.CreateHandoffBuilderWith(triageAgent)
        .WithHandoffs(triageAgent, [statusAgent, returnAgent, refundAgent])
        .WithHandoff(statusAgent, triageAgent, "Transfer to this agent if the issue is not status related")
        .WithHandoff(returnAgent, triageAgent, "Transfer to this agent if the issue is not return related")
        .WithHandoff(refundAgent, triageAgent, "Transfer to this agent if the issue is not refund related")
        .Build();

    // Run the workflow
    List<ChatMessage> messages = [];
    foreach (var query in Queries)
    {
        Console.WriteLine($"User: {query}");
        messages.Add(new(ChatRole.User, query));

        await using var run = await InProcessExecution.StreamAsync(handoffAgentWorkflow, messages);
        await run.TrySendMessageAsync(new TurnToken(emitEvents: true));

        string? lastExecutorId = null;
        await foreach (WorkflowEvent evt in run.WatchStreamAsync().ConfigureAwait(false))
        {
            if (evt is AgentRunUpdateEvent e)
            {
                if (string.IsNullOrEmpty(e.Update.Text) && e.Update.Contents.Count == 0)
                {
                    continue;
                }

                if (e.ExecutorId != lastExecutorId)
                {
                    lastExecutorId = e.ExecutorId;
                    Console.WriteLine();
                    Console.Write($"{e.Update.AuthorName}: ");
                }

                Console.Write(e.Update.Text);

                if (e.Update.Contents.OfType<Microsoft.Extensions.AI.FunctionCallContent>().FirstOrDefault()
                        is Microsoft.Extensions.AI.FunctionCallContent call)
                {
                    Console.WriteLine();
                    Console.WriteLine($"Calling function '{call.Name}' with arguments: {JsonSerializer.Serialize(call.Arguments)}");
                }
            }
            else if (evt is WorkflowOutputEvent output)
            {
                Console.WriteLine("\n");
                messages.AddRange(output.As<List<ChatMessage>>()!);
            }
        }
    }
}
# endregion

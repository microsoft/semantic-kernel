// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.Agents.Persistent;
using Azure.Identity;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.Agents.Magentic;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrates how to use the <see cref="MagenticOrchestration"/> with two agents:
/// - A Research agent that can perform web searches
/// - A Coder agent that can run code using the code interpreter
/// </summary>
public class Step05_Magentic(ITestOutputHelper output) : BaseOrchestrationTest(output)
{
    private const string ManagerModel = "o3-mini";
    private const string ResearcherModel = "gpt-4o-search-preview";

    /// <summary>
    /// Require OpenAI services in order to use "gpt-4o-search-preview" model
    /// </summary>
    protected override bool ForceOpenAI => true;

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task MagenticTaskAsync(bool streamedResponse)
    {
        // Define the agents
        Kernel researchKernel = CreateKernelWithOpenAIChatCompletion(ResearcherModel);
        ChatCompletionAgent researchAgent =
            this.CreateAgent(
                name: "ResearchAgent",
                description: "A helpful assistant with access to web search. Ask it to perform web searches.",
                instructions: "You are a Researcher. You find information without additional computation or quantitative analysis.",
                kernel: researchKernel);

        PersistentAgentsClient agentsClient = AzureAIAgent.CreateAgentsClient(TestConfiguration.AzureAI.Endpoint, new AzureCliCredential());
        PersistentAgent definition =
            await agentsClient.Administration.CreateAgentAsync(
                TestConfiguration.AzureAI.ChatModelId,
                name: "CoderAgent",
                description: "Write and executes code to process and analyze data.",
                instructions: "You solve questions using code. Please provide detailed analysis and computation process.",
                tools: [new CodeInterpreterToolDefinition()]);
        AzureAIAgent coderAgent = new(definition, agentsClient);

        // Create a monitor to capturing agent responses (via ResponseCallback)
        // to display at the end of this sample. (optional)
        // NOTE: Create your own callback to capture responses in your application or service.
        OrchestrationMonitor monitor = new();
        // Define the orchestration
        Kernel managerKernel = this.CreateKernelWithChatCompletion(ManagerModel);
        StandardMagenticManager manager =
            new(managerKernel.GetRequiredService<IChatCompletionService>(), new OpenAIPromptExecutionSettings())
            {
                MaximumInvocationCount = 5,
            };
        MagenticOrchestration orchestration =
            new(manager, researchAgent, coderAgent)
            {
                LoggerFactory = this.LoggerFactory,
                ResponseCallback = monitor.ResponseCallback,
                StreamingResponseCallback = streamedResponse ? monitor.StreamingResultCallback : null,
            };

        // Start the runtime
        InProcessRuntime runtime = new();
        await runtime.StartAsync();

        string input =
            """
            I am preparing a report on the energy efficiency of different machine learning model architectures.
            Compare the estimated training and inference energy consumption of ResNet-50, BERT-base, and GPT-2 on standard datasets
            (e.g., ImageNet for ResNet, GLUE for BERT, WebText for GPT-2).
            Then, estimate the CO2 emissions associated with each, assuming training on an Azure Standard_NC6s_v3 VM for 24 hours.
            Provide tables for clarity, and recommend the most energy-efficient model per task type
            (image classification, text classification, and text generation).
            """;
        Console.WriteLine($"\n# INPUT:\n{input}\n");
        OrchestrationResult<string> result = await orchestration.InvokeAsync(input, runtime);
        string text = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds * 10));
        Console.WriteLine($"\n# RESULT: {text}");

        await runtime.RunUntilIdleAsync();

        Console.WriteLine("\n\nORCHESTRATION HISTORY");
        foreach (ChatMessageContent message in monitor.History)
        {
            this.WriteAgentChatMessage(message);
        }
    }

    private Kernel CreateKernelWithOpenAIChatCompletion(string model)
    {
        IKernelBuilder builder = Kernel.CreateBuilder();

        builder.AddOpenAIChatCompletion(
            model,
            TestConfiguration.OpenAI.ApiKey);

        return builder.Build();
    }
}

// Copyright (c) Microsoft. All rights reserved.

using Azure.Identity;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.Agents.Magentic;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using AAIP = Azure.AI.Projects;

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

    [Fact]
    public async Task MagenticTaskAsync()
    {
        // Define the agents
        Kernel researchKernel = CreateKernelWithOpenAIChatCompletion(ResearcherModel);
        ChatCompletionAgent researchAgent =
            this.CreateAgent(
                name: "ResearchAgent",
                description: "Able to retrieve information and data from the Internet. Ask it to provide information or data without additional computation or quantitative analysis.",
                instructions: "Retrieve information and data from the Internet without additional computation or quantitative analysis.",
                kernel: researchKernel);

        AAIP.AIProjectClient projectClient = AzureAIAgent.CreateAzureAIClient(TestConfiguration.AzureAI.ConnectionString, new AzureCliCredential());
        AAIP.AgentsClient agentsClient = projectClient.GetAgentsClient();
        AAIP.Agent definition =
            await agentsClient.CreateAgentAsync(
                TestConfiguration.AzureAI.ChatModelId,
                name: "CoderAgent",
                description: "Write and executes code to process and analyze data.",
                instructions: "Use code to process and analyze data.",
                tools: [new Azure.AI.Projects.CodeInterpreterToolDefinition()]);
        AzureAIAgent coderAgent = new(definition, agentsClient);

        // Define the orchestration
        OrchestrationMonitor monitor = new();
        Kernel managerKernel = this.CreateKernelWithChatCompletion(ManagerModel);
        StandardMagenticManager manager =
            new(managerKernel.GetRequiredService<IChatCompletionService>(), new OpenAIPromptExecutionSettings())
            {
                MaximumInvocationCount = 5,
            };
        MagenticOrchestration orchestration =
            new(manager, researchAgent, coderAgent)
            {
                ResponseCallback = monitor.ResponseCallback,
                LoggerFactory = this.LoggerFactory,
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
        //string text = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds * 6));
        string text = await result.GetValueAsync();
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

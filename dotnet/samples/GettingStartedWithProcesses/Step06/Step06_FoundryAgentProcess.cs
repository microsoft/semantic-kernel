// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using Azure.Identity;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.Agents.OpenAI;
using OpenAI;

namespace Step06;
public class Step06_FoundryAgentProcess : BaseTest
{
    public Step06_FoundryAgentProcess(ITestOutputHelper output) : base(output, redirectSystemConsoleOutput: true)
    {
        this.Client =
            this.UseOpenAIConfig ?
                OpenAIAssistantAgent.CreateOpenAIClient(new ApiKeyCredential(this.ApiKey ?? throw new ConfigurationNotFoundException("OpenAI:ApiKey"))) :
                !string.IsNullOrWhiteSpace(this.ApiKey) ?
                    OpenAIAssistantAgent.CreateAzureOpenAIClient(new ApiKeyCredential(this.ApiKey), new Uri(this.Endpoint!)) :
                    OpenAIAssistantAgent.CreateAzureOpenAIClient(new AzureCliCredential(), new Uri(this.Endpoint!));
    }

    protected OpenAIClient Client { get; init; }

    // Target Open AI Services
    protected override bool ForceOpenAI => true;

    [Fact]
    public async Task ProcessWithExistingFoundryAgentsAndSeparateThreadsAsync()
    {
        var foundryAgentDefinition1 = new AgentDefinition { Id = "asst_6q5jvZmSxGaGwkiqPv1OmrdA", Name = "Agent1", Type = AzureAIAgentFactory.AzureAIAgentType };
        var foundryAgentDefinition2 = new AgentDefinition { Id = "asst_bM0sHsmAmNhEMj2nxKgPCiYr", Name = "Agent2", Type = AzureAIAgentFactory.AzureAIAgentType };

        var processBuilder = new FoundryProcessBuilder("foundry_agents");

        var agent1 = processBuilder.AddStepFromAgent(foundryAgentDefinition1)
            .OnComplete([new DeclarativeProcessCondition { Type = "Default", Emits = [new EventEmission() { EventType = "Agent1Complete" }] }]);

        var agent2 = processBuilder.AddStepFromAgent(foundryAgentDefinition2)
            .OnComplete([new DeclarativeProcessCondition { Type = "Default", Emits = [new EventEmission() { EventType = "Agent2Complete" }] }]);

        processBuilder.OnInputEvent("start").SendEventTo(new(agent1)); // Change to ListenForInput?

        processBuilder.ListenFor().Message("Agent1Complete", agent1).SendEventTo(new(agent2, (output) => output));
        processBuilder.ListenFor().Message("Agent2Complete", agent2).StopProcess();

        var process = processBuilder.Build();

        var foundryClient = AzureAIAgent.CreateAzureAIClient(TestConfiguration.AzureAI.ConnectionString, new AzureCliCredential());
        var agentsClient = foundryClient.GetAgentsClient();

        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddSingleton(agentsClient);
        kernelBuilder.Services.AddSingleton(foundryClient);
        var kernel = kernelBuilder.Build();

        var context = await process.StartAsync(kernel, new() { Id = "start", Data = "Why are frogs green?" });
        var agent1Result = await context.GetStateAsync();

        Assert.NotNull(context);
        Assert.NotNull(agent1Result);
    }

    [Fact]
    public async Task ProcessWithExistingFoundryAgentsAndSharedThreadAsync()
    {
        var foundryAgentDefinition1 = new AgentDefinition { Id = "asst_6q5jvZmSxGaGwkiqPv1OmrdA", Name = "Agent1", Type = AzureAIAgentFactory.AzureAIAgentType };
        var foundryAgentDefinition2 = new AgentDefinition { Id = "asst_bM0sHsmAmNhEMj2nxKgPCiYr", Name = "Agent2", Type = AzureAIAgentFactory.AzureAIAgentType };

        var processBuilder = new FoundryProcessBuilder("foundry_agents");

        processBuilder.AddThread("shared_thread", KernelProcessThreadLifetime.Scoped);

        var agent1 = processBuilder.AddStepFromAgent(foundryAgentDefinition1, threadName: "shared_thread")
            .OnComplete([new DeclarativeProcessCondition { Type = "Default", Emits = [new EventEmission() { EventType = "Agent1Complete" }] }]);

        var agent2 = processBuilder.AddStepFromAgent(foundryAgentDefinition2, threadName: "shared_thread")
            .OnComplete([new DeclarativeProcessCondition { Type = "Default", Emits = [new EventEmission() { EventType = "Agent2Complete" }] }]);

        processBuilder.OnInputEvent("start").SendEventTo(new(agent1));

        processBuilder.ListenFor().Message("Agent1Complete", agent1).SendEventTo(new(agent2, (output) => output));
        processBuilder.ListenFor().Message("Agent2Complete", agent2).StopProcess();

        var process = processBuilder.Build();

        var foundryClient = AzureAIAgent.CreateAzureAIClient(TestConfiguration.AzureAI.ConnectionString, new AzureCliCredential());
        var agentsClient = foundryClient.GetAgentsClient();

        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddSingleton(agentsClient);
        kernelBuilder.Services.AddSingleton(foundryClient);
        var kernel = kernelBuilder.Build();

        var context = await process.StartAsync(kernel, new() { Id = "start", Data = "Why are frogs green?" });
        var agent1Result = await context.GetStateAsync();

        Assert.NotNull(context);
        Assert.NotNull(agent1Result);
    }

    [Fact]
    public async Task ProcessWithExistingFoundryAgentsWithProcessStateUpdate()
    {
        // Define the agents
        var foundryAgentDefinition1 = new AgentDefinition { Id = "asst_6q5jvZmSxGaGwkiqPv1OmrdA", Name = "Agent1", Type = AzureAIAgentFactory.AzureAIAgentType };
        var foundryAgentDefinition2 = new AgentDefinition { Id = "asst_bM0sHsmAmNhEMj2nxKgPCiYr", Name = "Agent2", Type = AzureAIAgentFactory.AzureAIAgentType };

        // Define the process with a state type
        var processBuilder = new FoundryProcessBuilder("foundry_agents", stateType: typeof(ProcessStateWithCounter));
        processBuilder.AddThread("shared_thread", KernelProcessThreadLifetime.Scoped);

        var agent1 = processBuilder.AddStepFromAgent(foundryAgentDefinition1, threadName: "shared_thread")
            .WithMessageInput()
            .OnComplete([
            new DeclarativeProcessCondition
            {
                Type = "State",
                Expression = "Counter < `3`",
                Updates = [new VariableUpdate() { Path = "Counter", Operation = StateUpdateOperations.Increment, Value = 1 }],
                Emits = [new EventEmission() { EventType = "Agent1Retry" }]
            },
            new DeclarativeProcessCondition
            {
                Type = "State",
                Expression = "Counter >= `3`",
                Emits = [new EventEmission() { EventType = "Agent1Complete" }]
            }]);

        var agent2 = processBuilder.AddStepFromAgent(foundryAgentDefinition2, threadName: "shared_thread")
            .OnComplete([new DeclarativeProcessCondition { Type = "Default", Emits = [new EventEmission() { EventType = "Agent2Complete" }] }]);

        processBuilder.OnInputEvent("start").SendEventTo(new(agent1));

        processBuilder.ListenFor().Message("Agent1Retry", agent1).SendEventTo(new(agent1));
        processBuilder.ListenFor().Message("Agent1Complete", agent1).SendEventTo(new(agent2));
        processBuilder.ListenFor().Message("Agent2Complete", agent2).StopProcess();

        var process = processBuilder.Build();

        //var foundryClient = AzureAIAgent.CreateAzureAIClient(TestConfiguration.AzureAI.ConnectionString, new AzureCliCredential());
        //var agentsClient = foundryClient.GetAgentsClient();

        //var kernelBuilder = Kernel.CreateBuilder();
        //kernelBuilder.Services.AddSingleton(agentsClient);
        //kernelBuilder.Services.AddSingleton(foundryClient);
        //var kernel = kernelBuilder.Build();

        //var context = await process.StartAsync(kernel, new() { Id = "start", Data = "Why are frogs green?" });
        //var agent1Result = await context.GetStateAsync();

        //Assert.NotNull(context);
        //Assert.NotNull(agent1Result);

        var workflow = await WorkflowBuilder.BuildWorkflow(process);
        string yaml = WorkflowSerializer.SerializeToYaml(workflow);
    }

    public class ProcessStateWithCounter
    {
        public int Counter { get; set; }
    }

    //[Fact]
    //public async Task ProcessWithDeepResearch()
    //{
    //    string ledgerFactsAgentId = "";
    //    string ledgerFactsUpdateAgentId = "";
    //    string ledgerPlannerAgentId = "";
    //    string ledegerPlannerUpdateAgentId = "";
    //    string progressManagerAgentId = "";
    //    string actionRouterAgentId = "";
    //    string summarizerAgentId = "";
    //    string userAgentId = "";

    //    var processBuilder = new FoundryProcessBuilder("foundry_agents", stateType: typeof(DeepResearchState));

    //    //Define Threads
    //    var planThread = processBuilder.AddThread("plan");
    //    var runThread = processBuilder.AddThread("run");

    //    // Define the steps
    //    var gatherFactsStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = ledgerFactsAgentId, Name = "LedgerFacts", Type = AzureAIAgentFactory.AzureAIAgentType }, threadName: "plan")
    //        .WithUserStateInput("Instructions")
    //        .OnComplete([
    //            new DeclarativeProcessCondition {
    //                Type = "Default",
    //                Updates = [
    //                    new() { Operation = StateUpdateOperations.Set, Path = "tasks", Value = "$output.Tasks" },
    //                    new() { Operation = StateUpdateOperations.Set, Path = "facts", Value = "$output.Facts" }
    //                ],
    //                Emits = [new EventEmission() { EventType = "LedgerFactsComplete" }]
    //            }
    //        ]);

    //    var plannerStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = ledgerPlannerAgentId, Name = "LedgerPlanner", Type = AzureAIAgentFactory.AzureAIAgentType }, threadName: "plan")
    //        .OnComplete([
    //            new DeclarativeProcessCondition {
    //                Type = "Default",
    //                Updates = [
    //                    new() { Operation = StateUpdateOperations.Set, Path = "plan", Value = "$output.Plan" },
    //                    new() { Operation = StateUpdateOperations.Set, Path = "nextStep", Value = "$output.NextStep" }
    //                ],
    //                Emits = [new EventEmission() { EventType = "LedgerPlannerComplete" }]
    //            }
    //        ]);
    //}

    //public class DeepResearchState
    //{
    //    public string Instructions { get; set; }

    //    public string Summary { get; set; }

    //    public string Team { get; set; }

    //    public ChatMessageContent Plan { get; set; }

    //    public ChatMessageContent NextStep { get; set; }

    //    public object Tasks { get; set; }

    //    public object Facts { get; set; }

    //    public List<string> SystemAgents { get; set; } = ["FinalStepAgent", "UserAgent", "LedgerFactsUpdate"];

    //    public string NextAgentId { get; set; }
    //}
}

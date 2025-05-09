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
            .OnComplete([new DeclarativeProcessCondition { Type = DeclarativeProcessConditionType.Default, Emits = [new EventEmission() { EventType = "Agent1Complete" }] }]);

        var agent2 = processBuilder.AddStepFromAgent(foundryAgentDefinition2)
            .OnComplete([new DeclarativeProcessCondition { Type = DeclarativeProcessConditionType.Default, Emits = [new EventEmission() { EventType = "Agent2Complete" }] }]);

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
            .OnComplete([new DeclarativeProcessCondition { Type = DeclarativeProcessConditionType.Default, Emits = [new EventEmission() { EventType = "Agent1Complete" }] }]);

        var agent2 = processBuilder.AddStepFromAgent(foundryAgentDefinition2, threadName: "shared_thread")
            .OnComplete([new DeclarativeProcessCondition { Type = DeclarativeProcessConditionType.Default, Emits = [new EventEmission() { EventType = "Agent2Complete" }] }]);

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
    public async Task ProcessWithExistingFoundryAgentsWithProcessStateUpdateAndOnCompleteConditions()
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
                Type = DeclarativeProcessConditionType.State,
                Expression = "Counter < `3`",
                Updates = [new VariableUpdate() { Path = "Counter", Operation = StateUpdateOperations.Increment, Value = 1 }],
                Emits = [new EventEmission() { EventType = "Agent1Retry" }]
            },
            new DeclarativeProcessCondition
            {
                Type = DeclarativeProcessConditionType.State,
                Expression = "Counter >= `3`",
                Emits = [new EventEmission() { EventType = "Agent1Complete" }]
            }]);

        var agent2 = processBuilder.AddStepFromAgent(foundryAgentDefinition2, threadName: "shared_thread")
            .OnComplete([new DeclarativeProcessCondition { Type = DeclarativeProcessConditionType.Default, Emits = [new EventEmission() { EventType = "Agent2Complete" }] }]);

        processBuilder.OnInputEvent("start").SendEventTo(new(agent1));

        processBuilder.ListenFor().Message("Agent1Retry", agent1).SendEventTo(new(agent1));
        processBuilder.ListenFor().Message("Agent1Complete", agent1).SendEventTo(new(agent2));
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

        var workflow = await WorkflowBuilder.BuildWorkflow(process);
        string yaml = WorkflowSerializer.SerializeToYaml(workflow);
    }

    [Fact]
    public async Task ProcessWithExistingFoundryAgentsWithProcessStateUpdateAndOrchestrationConditions()
    {
        // Define the agents
        var foundryAgentDefinition1 = new AgentDefinition { Id = "asst_6q5jvZmSxGaGwkiqPv1OmrdA", Name = "Agent1", Type = AzureAIAgentFactory.AzureAIAgentType };
        var foundryAgentDefinition2 = new AgentDefinition { Id = "asst_bM0sHsmAmNhEMj2nxKgPCiYr", Name = "Agent2", Type = AzureAIAgentFactory.AzureAIAgentType };

        // Define the process with a state type
        var processBuilder = new FoundryProcessBuilder("foundry_agents", stateType: typeof(ProcessStateWithCounter));
        processBuilder.AddThread("shared_thread", KernelProcessThreadLifetime.Scoped);

        // Agent1 will increment the Counter state variable every time it runs
        var agent1 = processBuilder.AddStepFromAgent(foundryAgentDefinition1, threadName: "shared_thread")
            .WithMessageInput()
            .OnComplete([
            new DeclarativeProcessCondition
            {
                Type = DeclarativeProcessConditionType.Default,
                Updates = [new VariableUpdate() { Path = "Counter", Operation = StateUpdateOperations.Increment, Value = 1 }],
            }]);

        var agent2 = processBuilder.AddStepFromAgent(foundryAgentDefinition2, threadName: "shared_thread");

        processBuilder.OnInputEvent("start").SendEventTo(new(agent1));

        // Agent1 should run as long as the Counter is less than 3
        processBuilder.ListenFor().OnResult(agent1, condition: "_state_.Counter < `3`").SendEventTo(new(agent1));

        // When the Counter is 3, Agent1 should stop and Agent2 should start
        processBuilder.ListenFor().OnResult(agent1, condition: "_state_.Counter >= `3`").SendEventTo(new(agent2));

        // When Agent2 is done, the process should stop
        processBuilder.ListenFor().OnResult(agent2).StopProcess();

        var process = processBuilder.Build();

        //var foundryClient = AzureAIAgent.CreateAzureAIClient(TestConfiguration.AzureAI.ConnectionString, new AzureCliCredential());
        //var agentsClient = foundryClient.GetAgentsClient();

        //var kernelBuilder = Kernel.CreateBuilder();
        //kernelBuilder.Services.AddSingleton(agentsClient);
        //kernelBuilder.Services.AddSingleton(foundryClient);
        //var kernel = kernelBuilder.Build();

        //var context = await process.StartAsync(kernel, new() { Id = "start", Data = "Why are distributed systems hard to reason about?" });
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

    [Fact]
    public async Task ProcessWithDeepResearch()
    {
        string ledgerFactsAgentId = "";
        string ledgerFactsUpdateAgentId = "";
        string ledgerPlannerAgentId = "";
        string ledegerPlannerUpdateAgentId = "";
        string progressManagerAgentId = "";
        string actionRouterAgentId = "";
        string summarizerAgentId = "";
        string userAgentId = "";

        var processBuilder = new FoundryProcessBuilder("foundry_agents", stateType: typeof(DeepResearchState));

        //Define Threads
        var planThread = processBuilder.AddThread("plan");
        var runThread = processBuilder.AddThread("run");

        // Define the steps
        var gatherFactsStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = ledgerFactsAgentId, Name = "LedgerFacts", Type = AzureAIAgentFactory.AzureAIAgentType }, threadName: "plan")
            .WithUserStateInput("Instructions")
            .OnComplete([
                new DeclarativeProcessCondition {
                    Type = DeclarativeProcessConditionType.Default,
                    Updates = [
                        new() { Operation = StateUpdateOperations.Set, Path = "Tasks", Value = "$output.tasks" },
                        new() { Operation = StateUpdateOperations.Set, Path = "Facts", Value = "$output.facts" }
                    ],
                }
            ]);

        var plannerStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = ledgerPlannerAgentId, Name = "LedgerPlanner", Type = AzureAIAgentFactory.AzureAIAgentType }, threadName: "plan")
            .OnComplete([
                new DeclarativeProcessCondition {
                    Type = DeclarativeProcessConditionType.Default,
                    Updates = [
                        new() { Operation = StateUpdateOperations.Set, Path = "plan", Value = "$output.Plan" },
                        new() { Operation = StateUpdateOperations.Set, Path = "nextStep", Value = "$output.NextStep" }
                    ],
                }
            ]);

        var progressManagerStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = progressManagerAgentId, Name = "ProgressManager", Type = AzureAIAgentFactory.AzureAIAgentType }, threadName: "run")
            .OnComplete([
                new DeclarativeProcessCondition {
                    Type = DeclarativeProcessConditionType.Default,
                    Updates = [
                        new() { Operation = StateUpdateOperations.Set, Path = "NextStep", Value = "$output" }
                    ],
                }
            ]);

        var routerStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = actionRouterAgentId, Name = "ActionRouter", Type = AzureAIAgentFactory.AzureAIAgentType }, threadName: "run")
            .OnComplete([
                new DeclarativeProcessCondition {
                    Type = DeclarativeProcessConditionType.Default,
                    Updates = [
                        new() { Operation = StateUpdateOperations.Set, Path = "NextAgentId", Value = "$output.targetAgentId" }
                    ],
                }
            ]);

        // Dynamic Step?
        var dynamicStep = processBuilder.AddStepFromAgentProxy(new AgentDefinition { Id = "_state_.NextAgentId", Name = "DynamicStep", Type = AzureAIAgentFactory.AzureAIAgentType }, threadName: "run")
            .OnComplete([
                new DeclarativeProcessCondition {
                    Type = DeclarativeProcessConditionType.Default,
                    Updates = [
                        new() { Operation = StateUpdateOperations.Set, Path = "NextAgentId", Value = "$output.targetAgentId" }
                    ],
                }
            ]);

        // UserAgentStep TODO: HITL
        var userAgentStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = userAgentId, Name = "UserAgent", Type = AzureAIAgentFactory.AzureAIAgentType }, threadName: "run")
            .OnComplete([
                new DeclarativeProcessCondition {
                    Type = DeclarativeProcessConditionType.Default,
                    Updates = [
                        new() { Operation = StateUpdateOperations.Set, Path = "NextAgentId", Value = "$output.targetAgentId" }
                    ],
                }
            ]);

        var summarizerStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = summarizerAgentId, Name = "Summarizer", Type = AzureAIAgentFactory.AzureAIAgentType }, threadName: "run")
            .OnComplete([
                new DeclarativeProcessCondition {
                    Type = DeclarativeProcessConditionType.Default,
                    Updates = [
                        new() { Operation = StateUpdateOperations.Set, Path = "Summary", Value = "$output.summary" }
                    ],
                }
            ]);

        var factUpdateStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = ledgerFactsUpdateAgentId, Name = "LedgerFactsUpdate", Type = AzureAIAgentFactory.AzureAIAgentType }, threadName: "run");

        var planUpdateStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = ledegerPlannerUpdateAgentId, Name = "LedgerPlannerUpdate", Type = AzureAIAgentFactory.AzureAIAgentType }, threadName: "run");

        //Start -> Gaether Facts
        processBuilder.OnInputEvent("start")
            .SendEventTo(new(gatherFactsStep));

        //Gather Facts -> Planner
        processBuilder.ListenFor().OnResult(gatherFactsStep).SendEventTo(new(plannerStep));

        //Planner -> Progress Manager
        processBuilder.ListenFor().OnResult(plannerStep).SendEventTo(new(progressManagerStep));

        //Progress Manager -> Router
        processBuilder.ListenFor().OnResult(progressManagerStep).SendEventTo(new(routerStep));

        //Router -> Progress Manager
        processBuilder.ListenFor().OnResult(routerStep, condition: "contains(_state_.NextAgentId, 'UnknownAgent')").SendEventTo(new(progressManagerStep));

        //Router -> Facts Update
        processBuilder.ListenFor().OnResult(routerStep, condition: "contains(_state_.NextAgentId, 'LedgerFactsUpdate')").SendEventTo(new(factUpdateStep));

        //Router -> User Agent
        processBuilder.ListenFor().OnResult(routerStep, condition: "contains(_state_.NextAgentId, 'UserAgent')").SendEventTo(new(userAgentStep));

        //Router -> Summarizer
        processBuilder.ListenFor().OnResult(routerStep, condition: "contains(_state_.NextAgentId, 'Summarizer')").SendEventTo(new(summarizerStep));

        //Router -> Dynamic Step
        processBuilder.ListenFor().OnResult(routerStep, condition: "!contains(_state_.NextAgentId, 'FinalStepAgent')").SendEventTo(new(dynamicStep));

        //Dynamic Step -> Progress Manager
        processBuilder.ListenFor().OnResult(dynamicStep).SendEventTo(new(progressManagerStep));

        //Facts Update -> Plan Update
        processBuilder.ListenFor().OnResult(factUpdateStep).SendEventTo(new(planUpdateStep));

        //PlanUpdate -> Progress Manager
        processBuilder.ListenFor().OnResult(planUpdateStep).SendEventTo(new(progressManagerStep));

        //Summarizer -> End
        processBuilder.ListenFor().OnResult(summarizerStep).StopProcess();
    }

    public class DeepResearchState
    {
        public string Instructions { get; set; }

        public string Summary { get; set; }

        public string Team { get; set; }

        public ChatMessageContent Plan { get; set; }

        public ChatMessageContent NextStep { get; set; }

        public object Tasks { get; set; }

        public object Facts { get; set; }

        public List<string> SystemAgents { get; set; } = ["FinalStepAgent", "UserAgent", "LedgerFactsUpdate"];

        public string NextAgentId { get; set; }
    }
}

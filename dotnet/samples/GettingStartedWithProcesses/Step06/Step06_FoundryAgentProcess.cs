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

        var agent1 = processBuilder.AddStepFromAgent(foundryAgentDefinition1, defaultThread: "shared_thread")
            .OnComplete([new DeclarativeProcessCondition { Type = DeclarativeProcessConditionType.Default, Emits = [new EventEmission() { EventType = "Agent1Complete" }] }]);

        var agent2 = processBuilder.AddStepFromAgent(foundryAgentDefinition2, defaultThread: "shared_thread")
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
        var processBuilder = new FoundryProcessBuilder<ProcessStateWithCounter>("foundry_agents");
        processBuilder.AddThread("shared_thread", KernelProcessThreadLifetime.Scoped);

        var agent1 = processBuilder.AddStepFromAgent(foundryAgentDefinition1, defaultThread: "shared_thread")
            .OnComplete([
            new DeclarativeProcessCondition
            {
                Type = DeclarativeProcessConditionType.Eval,
                Expression = "Counter < `3`",
                Updates = [new VariableUpdate() { Path = "Counter", Operation = StateUpdateOperations.Increment, Value = 1 }],
                Emits = [new EventEmission() { EventType = "Agent1Retry" }]
            },
            new DeclarativeProcessCondition
            {
                Type = DeclarativeProcessConditionType.Eval,
                Expression = "Counter >= `3`",
                Emits = [new EventEmission() { EventType = "Agent1Complete" }]
            }]);

        var agent2 = processBuilder.AddStepFromAgent(foundryAgentDefinition2, defaultThread: "shared_thread")
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
        var processBuilder = new FoundryProcessBuilder<ProcessStateWithCounter>("foundry_agents");
        processBuilder.AddThread("shared_thread", KernelProcessThreadLifetime.Scoped);

        // Agent1 will increment the Counter state variable every time it runs
        var agent1 = processBuilder.AddStepFromAgent(foundryAgentDefinition1, defaultThread: "shared_thread")
            .OnComplete([
            new DeclarativeProcessCondition
            {
                Type = DeclarativeProcessConditionType.Default,
                Updates = [new VariableUpdate() { Path = "Counter", Operation = StateUpdateOperations.Increment, Value = 1 }],
            }]);

        var agent2 = processBuilder.AddStepFromAgent(foundryAgentDefinition2, defaultThread: "shared_thread");

        processBuilder.OnInputEvent("start").SendEventTo(new(agent1));

        // Agent1 should run as long as the Counter is less than 3
        processBuilder.ListenFor().OnResult(agent1, condition: "_variables_.Counter < `3`").SendEventTo(new(agent1));

        // When the Counter is 3, Agent1 should stop and Agent2 should start
        processBuilder.ListenFor().OnResult(agent1, condition: "_variables_.Counter >= `3`").SendEventTo(new(agent2));

        // When Agent2 is done, the process should stop
        processBuilder.ListenFor().OnResult(agent2).StopProcess();

        var process = processBuilder.Build();

        var foundryClient = AzureAIAgent.CreateAzureAIClient(TestConfiguration.AzureAI.ConnectionString, new AzureCliCredential());
        var agentsClient = foundryClient.GetAgentsClient();

        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddSingleton(agentsClient);
        kernelBuilder.Services.AddSingleton(foundryClient);
        var kernel = kernelBuilder.Build();

        var context = await process.StartAsync(kernel, new() { Id = "start", Data = "Why are distributed systems hard to reason about?" });
        var agent1Result = await context.GetStateAsync();

        Assert.NotNull(context);
        Assert.NotNull(agent1Result);

        var workflow = await WorkflowBuilder.BuildWorkflow(process);
        string yaml = WorkflowSerializer.SerializeToYaml(workflow);
    }

    [Fact]
    public async Task ProcessWithExistingFoundryAgentsWithDynamicAgentResolution()
    {
        // Define the agents
        var foundryAgentDefinition1 = new AgentDefinition { Id = "asst_6q5jvZmSxGaGwkiqPv1OmrdA", Name = "Agent1", Type = AzureAIAgentFactory.AzureAIAgentType };
        var foundryAgentDefinition2 = new AgentDefinition { Id = "_variables_.NextAgentId", Name = "Agent2", Type = AzureAIAgentFactory.AzureAIAgentType };

        // Define the process with a state type
        var processBuilder = new FoundryProcessBuilder<DynamicAgentState>("foundry_agents");
        processBuilder.AddThread("shared_thread", KernelProcessThreadLifetime.Scoped);

        // Agent1 will increment the Counter state variable every time it runs
        var agent1 = processBuilder.AddStepFromAgent(foundryAgentDefinition1, defaultThread: "shared_thread")
            .OnComplete([
            new DeclarativeProcessCondition
            {
                Type = DeclarativeProcessConditionType.Default,
                Updates = [new VariableUpdate() { Path = "Counter", Operation = StateUpdateOperations.Increment, Value = 1 }],
            }]);

        var agent2 = processBuilder.AddStepFromAgentProxy(stepId: "dynamicAgent", foundryAgentDefinition2, threadName: "shared_thread");

        processBuilder.OnInputEvent("start").SendEventTo(new(agent1));

        // Agent1 should run as long as the Counter is less than 3
        processBuilder.ListenFor().OnResult(agent1, condition: "_variables_.Counter < `3`").SendEventTo(new(agent1));

        // When the Counter is 3, Agent1 should stop and Agent2 should start
        processBuilder.ListenFor().OnResult(agent1, condition: "_variables_.Counter >= `3`").SendEventTo(new(agent2));

        // When Agent2 is done, the process should stop
        processBuilder.ListenFor().OnResult(agent2).StopProcess();

        var process = processBuilder.Build();

        var foundryClient = AzureAIAgent.CreateAzureAIClient(TestConfiguration.AzureAI.ConnectionString, new AzureCliCredential());
        var agentsClient = foundryClient.GetAgentsClient();

        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddSingleton(agentsClient);
        kernelBuilder.Services.AddSingleton(foundryClient);
        var kernel = kernelBuilder.Build();

        var context = await process.StartAsync(kernel, new() { Id = "start", Data = "Why are distributed systems hard to reason about?" });
        var agent1Result = await context.GetStateAsync();

        Assert.NotNull(context);
        Assert.NotNull(agent1Result);

        var workflow = await WorkflowBuilder.BuildWorkflow(process);
        string yaml = WorkflowSerializer.SerializeToYaml(workflow);
    }

    [Fact]
    public async Task ProcessWithTwoAgentMathChat()
    {
        // Define the agents
        var studentDefinition = new AgentDefinition { Id = "asst_6q5jvZmSxGaGwkiqPv1OmrdA", Name = "Student", Type = AzureAIAgentFactory.AzureAIAgentType };
        var teacherDefinition = new AgentDefinition { Id = "asst_bM0sHsmAmNhEMj2nxKgPCiYr", Name = "Teacher", Type = AzureAIAgentFactory.AzureAIAgentType };

        // Define the process with a state type
        var processBuilder = new FoundryProcessBuilder<TwoAgentMathState>("two_agent_math_chat");

        // Create a thread for the student
        processBuilder.AddThread("student_thread", KernelProcessThreadLifetime.Scoped);

        // Add the student
        var student = processBuilder.AddStepFromAgent(studentDefinition);

        // Add the teacher
        var teacher = processBuilder.AddStepFromAgent(teacherDefinition);

        // Orchestrate
        processBuilder.ListenFor().InputEvent("start").SendEventToAgent(
            student,
            thread: "_variables_.StudentThread",
            messagesIn: "_variables_.TeacherMessages",
            inputs: new Dictionary<string, string>
            {
                { "InteractionCount", "_variables_.StudentState.InteractionCount" }
            });

        processBuilder.ListenFor().OnResult(student)
            .Update(new() { Path = "_variables_.StudentMessages", Operation = StateUpdateOperations.Set, Value = "_agent_.messages_out" })
            .Update(new() { Path = "_variables_.UserMessages", Operation = StateUpdateOperations.Increment, Value = "_agent_.user_messages" })
            .Update(new() { Path = "_variables_.InteractionCount", Operation = StateUpdateOperations.Increment, Value = "_agent_.student_messages" })
            .Update(new() { Path = "_variables_.StudentState.InteractionCount", Operation = StateUpdateOperations.Increment, Value = "_agent_.student_messages" })
            .Update(new() { Path = "_variables_.StudentState.Name", Operation = StateUpdateOperations.Set, Value = "Runhan" })
            .SendEventToAgent(teacher, messagesIn: "_variables_.StudentMessages");

        processBuilder.ListenFor().OnResult(teacher, condition: "contains(to_string(_agent_.messages_out), '[COMPLETE]')")
            .Update(new() { Path = "_variables_.TeacherMessages", Operation = StateUpdateOperations.Set, Value = "_agent_.messages_out" })
            .Update(new() { Path = "_variables_.InteractionCount", Operation = StateUpdateOperations.Increment, Value = 1 });

        processBuilder.ListenFor().OnResult(teacher, condition: "_default_")
            .SendEventToAgent(student);

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

    public class TwoAgentMathState
    {
        public List<ChatMessageContent> UserMessages { get; set; }

        public List<ChatMessageContent> StudentMessages { get; set; }

        public List<ChatMessageContent> TeacherMessages { get; set; }

        public StudentState StudentState { get; set; } = new();

        public int InteractionCount { get; set; }
    }

    public class StudentState
    {
        public int InteractionCount { get; set; }

        public string Name { get; set; }
    }

    [Fact]
    public async Task ProcessWithDeepResearch()
    {
        string ledgerFactsAgentId = nameof(ledgerFactsAgentId);
        string ledgerFactsUpdateAgentId = nameof(ledgerFactsUpdateAgentId);
        string ledgerPlannerAgentId = nameof(ledgerPlannerAgentId);
        string ledgerPlannerUpdateAgentId = nameof(ledgerPlannerUpdateAgentId);
        string progressManagerAgentId = nameof(progressManagerAgentId);
        string actionRouterAgentId = nameof(actionRouterAgentId);
        string summarizerAgentId = nameof(summarizerAgentId);
        string userAgentId = nameof(userAgentId);

        var processBuilder = new FoundryProcessBuilder<DeepResearchState>("foundry_agents");

        //Define Threads
        var planThread = processBuilder.AddThread("plan");
        var runThread = processBuilder.AddThread("run");

        // Define the steps
        var gatherFactsStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = ledgerFactsAgentId, Name = "LedgerFacts", Type = AzureAIAgentFactory.AzureAIAgentType }, defaultThread: "plan")
            .WithUserStateInput((state) => state.Instructions)
            .OnComplete([
                new DeclarativeProcessCondition {
                    Type = DeclarativeProcessConditionType.Default,
                    Updates = [
                        new() { Operation = StateUpdateOperations.Set, Path = "Tasks", Value = "_agent_.outputs.tasks" },
                        new() { Operation = StateUpdateOperations.Set, Path = "Facts", Value = "_agent_.outputs.facts" }
                    ],
                }
            ]);

        var plannerStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = ledgerPlannerAgentId, Name = "LedgerPlanner", Type = AzureAIAgentFactory.AzureAIAgentType }, defaultThread: "plan")
            .OnComplete([
                new DeclarativeProcessCondition {
                    Type = DeclarativeProcessConditionType.Default,
                    Updates = [
                        new() { Operation = StateUpdateOperations.Set, Path = "plan", Value = "_agent_.outputs.Plan" },
                        new() { Operation = StateUpdateOperations.Set, Path = "nextStep", Value = "_agent_.outputs.NextStep" }
                    ],
                }
            ]);

        var progressManagerStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = progressManagerAgentId, Name = "ProgressManager", Type = AzureAIAgentFactory.AzureAIAgentType }, defaultThread: "run")
            .OnComplete([
                new DeclarativeProcessCondition {
                    Type = DeclarativeProcessConditionType.Default,
                    Updates = [
                        new() { Operation = StateUpdateOperations.Set, Path = "NextStep", Value = "_agent_.outputs" }
                    ],
                }
            ]);

        var routerStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = actionRouterAgentId, Name = "ActionRouter", Type = AzureAIAgentFactory.AzureAIAgentType }, defaultThread: "run")
            .OnComplete([
                new DeclarativeProcessCondition {
                    Type = DeclarativeProcessConditionType.Default,
                    Updates = [
                        new() { Operation = StateUpdateOperations.Set, Path = "NextAgentId", Value = "_agent_.outputs.targetAgentId" }
                    ],
                }
            ]);

        // Dynamic Step
        var dynamicStep = processBuilder.AddStepFromAgentProxy(stepId: "dynamicAgent", new AgentDefinition { Id = "_variables_.NextAgentId", Name = "DynamicStep", Type = AzureAIAgentFactory.AzureAIAgentType }, threadName: "run")
            .OnComplete([
                new DeclarativeProcessCondition {
                    Type = DeclarativeProcessConditionType.Default,
                    Updates = [
                        new() { Operation = StateUpdateOperations.Set, Path = "NextAgentId", Value = "_agent_.outputs.targetAgentId" }
                    ],
                }
            ]);

        // UserAgentStep
        var userAgentStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = userAgentId, Name = "UserAgent", Type = AzureAIAgentFactory.AzureAIAgentType }, defaultThread: "run", humanInLoopMode: HITLMode.Always)
            .OnComplete([
                new DeclarativeProcessCondition {
                    Type = DeclarativeProcessConditionType.Default,
                    Updates = [
                        new() { Operation = StateUpdateOperations.Set, Path = "NextAgentId", Value = "_agent_.outputs.targetAgentId" }
                    ],
                }
            ]);

        var summarizerStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = summarizerAgentId, Name = "Summarizer", Type = AzureAIAgentFactory.AzureAIAgentType }, defaultThread: "run")
            .OnComplete([
                new DeclarativeProcessCondition {
                    Type = DeclarativeProcessConditionType.Default,
                    Updates = [
                        new() { Operation = StateUpdateOperations.Set, Path = "Summary", Value = "_agent_.outputs.summary" }
                    ],
                }
            ]);

        var factUpdateStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = ledgerFactsUpdateAgentId, Name = "LedgerFactsUpdate", Type = AzureAIAgentFactory.AzureAIAgentType }, defaultThread: "run");

        var planUpdateStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = ledgerPlannerUpdateAgentId, Name = "LedgerPlannerUpdate", Type = AzureAIAgentFactory.AzureAIAgentType }, defaultThread: "run");

        //Start -> Gaether Facts
        processBuilder.OnInputEvent("start")
            .SendEventTo(new(gatherFactsStep));

        //Gather Facts -> Planner
        processBuilder.ListenFor().OnResult(gatherFactsStep).SendEventToAgent(plannerStep);

        //Planner -> Progress Manager
        processBuilder.ListenFor().OnResult(plannerStep).SendEventToAgent(progressManagerStep);

        //Progress Manager -> Router
        processBuilder.ListenFor().OnResult(progressManagerStep).SendEventToAgent(routerStep);

        //Router -> Progress Manager
        processBuilder.ListenFor().OnResult(routerStep, condition: "contains(_variables_.NextAgentId, 'UnknownAgent')").SendEventToAgent(progressManagerStep, inputs: new Dictionary<string, string> { { "arg1", "_variables_.NextAgentId" } }, messagesIn: "_variables_.Plan");

        //Router -> Facts Update
        processBuilder.ListenFor().OnResult(routerStep, condition: "contains(_variables_.NextAgentId, 'LedgerFactsUpdate')").SendEventToAgent(factUpdateStep);

        //Router -> User Agent
        processBuilder.ListenFor().OnResult(routerStep, condition: "contains(_variables_.NextAgentId, 'UserAgent')").SendEventToAgent(userAgentStep);

        //Router -> Summarizer
        processBuilder.ListenFor().OnResult(routerStep, condition: "contains(_variables_.NextAgentId, 'Summarizer')").SendEventToAgent(summarizerStep);

        //Router -> Dynamic Step
        processBuilder.ListenFor().OnResult(routerStep, condition: "!contains(_variables_.NextAgentId, 'FinalStepAgent')").SendEventToAgent(dynamicStep);

        //Dynamic Step -> Progress Manager
        processBuilder.ListenFor().OnResult(dynamicStep).SendEventToAgent(progressManagerStep);

        //Facts Update -> Plan Update
        processBuilder.ListenFor().OnResult(factUpdateStep).SendEventToAgent(planUpdateStep);

        //PlanUpdate -> Progress Manager
        processBuilder.ListenFor().OnResult(planUpdateStep).SendEventToAgent(progressManagerStep);

        //Summarizer -> End
        processBuilder.ListenFor().OnResult(summarizerStep).StopProcess();

        var process = processBuilder.Build();

        var workflow = await WorkflowBuilder.BuildWorkflow(process);
        string yaml = WorkflowSerializer.SerializeToYaml(workflow);
    }

    public class DeepResearchState
    {
        public string Instructions { get; set; }

        public string Summary { get; set; }

        public string Team { get; set; }

        public List<ChatMessageContent> Plan { get; set; }

        public List<ChatMessageContent> NextStep { get; set; }

        public object Tasks { get; set; }

        public object Facts { get; set; }

        public List<string> SystemAgents { get; set; } = ["FinalStepAgent", "UserAgent", "LedgerFactsUpdate"];

        public string NextAgentId { get; set; }
    }

    public class DynamicAgentState
    {
        public string NextAgentId { get; set; } = "asst_bM0sHsmAmNhEMj2nxKgPCiYr";
        public int Counter { get; set; }
    }

    public class ProcessStateWithCounter
    {
        public int Counter { get; set; }
    }
}

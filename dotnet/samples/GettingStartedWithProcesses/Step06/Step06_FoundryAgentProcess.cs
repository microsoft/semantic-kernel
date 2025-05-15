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

        var agent1 = processBuilder.AddStepFromAgent(foundryAgentDefinition1);
        var agent2 = processBuilder.AddStepFromAgent(foundryAgentDefinition2);

        processBuilder.OnProcessEnter().SendEventTo(agent1);
        processBuilder.OnResultFromStep(agent1).SendEventTo(agent2);
        processBuilder.OnResultFromStep(agent2).StopProcess();

        var process = processBuilder.Build();

        var foundryClient = AzureAIAgent.CreateAzureAIClient(TestConfiguration.AzureAI.ConnectionString, new AzureCliCredential());
        var agentsClient = foundryClient.GetAgentsClient();

        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddSingleton(agentsClient);
        kernelBuilder.Services.AddSingleton(foundryClient);
        var kernel = kernelBuilder.Build();
    }

    [Fact]
    public async Task ProcessWithExistingFoundryAgentsAndSharedThreadAsync()
    {
        var foundryAgentDefinition1 = new AgentDefinition { Id = "asst_6q5jvZmSxGaGwkiqPv1OmrdA", Name = "Agent1", Type = AzureAIAgentFactory.AzureAIAgentType };
        var foundryAgentDefinition2 = new AgentDefinition { Id = "asst_bM0sHsmAmNhEMj2nxKgPCiYr", Name = "Agent2", Type = AzureAIAgentFactory.AzureAIAgentType };

        var processBuilder = new FoundryProcessBuilder("foundry_agents");

        processBuilder.AddThread("shared_thread", KernelProcessThreadLifetime.Scoped);

        var agent1 = processBuilder.AddStepFromAgent(foundryAgentDefinition1, defaultThread: "shared_thread");
        var agent2 = processBuilder.AddStepFromAgent(foundryAgentDefinition2, defaultThread: "shared_thread");

        processBuilder.OnInputEvent("start").SendEventTo(new(agent1));

        processBuilder.OnResultFromStep(agent2);
        processBuilder.OnResultFromStep(agent2).StopProcess();

        var process = processBuilder.Build();

        var foundryClient = AzureAIAgent.CreateAzureAIClient(TestConfiguration.AzureAI.ConnectionString, new AzureCliCredential());
        var agentsClient = foundryClient.GetAgentsClient();

        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddSingleton(agentsClient);
        kernelBuilder.Services.AddSingleton(foundryClient);
        var kernel = kernelBuilder.Build();
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

        var agent1 = processBuilder.AddStepFromAgent(foundryAgentDefinition1, defaultThread: "shared_thread");
        var agent2 = processBuilder.AddStepFromAgent(foundryAgentDefinition2, defaultThread: "shared_thread");

        processBuilder.OnInputEvent("start").SendEventTo(new(agent1));

        processBuilder.OnResultFromStep(agent1, condition: "_variables_.Counter < `3`").SendEventTo(agent1);
        processBuilder.OnResultFromStep(agent1, condition: "_variables_.Counter >= `3`").SendEventTo(agent2);
        processBuilder.OnResultFromStep(agent2).StopProcess();

        var process = processBuilder.Build();
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
        var agent1 = processBuilder.AddStepFromAgent(foundryAgentDefinition1, defaultThread: "shared_thread");

        var agent2 = processBuilder.AddStepFromAgent(foundryAgentDefinition2, defaultThread: "shared_thread");

        processBuilder.OnProcessEnter().SendEventTo(agent1);

        // Increment the counter every time the step runs
        processBuilder.OnStepEnter(agent1, condition: "always").UpdateProcessState("Counter", StateUpdateOperations.Increment, 1);

        // Agent1 should run as long as the Counter is less than 3
        processBuilder.OnResultFromStep(agent1, condition: "_variables_.Counter < `3`").SendEventTo(agent1);

        // When the Counter is 3, Agent1 should stop and Agent2 should start
        processBuilder.OnResultFromStep(agent1, condition: "_variables_.Counter >= `3`").SendEventTo(agent2);

        // When Agent2 is done, the process should stop
        processBuilder.OnResultFromStep(agent2).StopProcess();

        var process = processBuilder.Build();
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
        var agent1 = processBuilder.AddStepFromAgent(foundryAgentDefinition1, defaultThread: "shared_thread");

        var agent2 = processBuilder.AddStepFromAgentProxy(stepId: "dynamicAgent", foundryAgentDefinition2, threadName: "shared_thread");

        processBuilder.OnInputEvent("start").SendEventTo(new(agent1));

        // Increment the counter every time the step runs
        processBuilder.OnStepEnter(agent1, condition: "always").UpdateProcessState("Counter", StateUpdateOperations.Increment, 1);

        // Agent1 should run as long as the Counter is less than 3
        processBuilder.OnResultFromStep(agent1, condition: "_variables_.Counter < `3`").SendEventTo(agent1);

        // When the Counter is 3, Agent1 should stop and Agent2 should start
        processBuilder.OnResultFromStep(agent1, condition: "_variables_.Counter >= `3`").SendEventTo(agent2);

        // When Agent2 is done, the process should stop
        processBuilder.OnResultFromStep(agent2).StopProcess();

        var process = processBuilder.Build();
    }

    [Fact]
    public async Task ProcessWithTwoAgentMathChat()
    {
        // Define the agents
        var studentDefinition = new AgentDefinition { Id = "asst_lGAOawWKaDEZp8XwNCF3ORlb", Name = "Student", Type = AzureAIAgentFactory.AzureAIAgentType };
        var teacherDefinition = new AgentDefinition { Id = "asst_7CPOY8YXbqNviklLKqylkEDD", Name = "Teacher", Type = AzureAIAgentFactory.AzureAIAgentType };

        // Define the process with a state type
        var processBuilder = new FoundryProcessBuilder<TwoAgentMathState>("two_agent_math_chat");

        // Create a thread for the student
        processBuilder.AddThread("student_thread", KernelProcessThreadLifetime.Scoped);

        // Add the student
        var student = processBuilder.AddStepFromAgent(studentDefinition);

        // Add the teacher
        var teacher = processBuilder.AddStepFromAgent(teacherDefinition);

        // Orchestrate
        processBuilder.OnProcessEnter().SendEventTo(
            student,
            thread: "_variables_.student_thread",
            messagesIn: ["_variables_.TeacherMessages"],
            inputs: new Dictionary<string, string>
            {
                { "InteractionCount", "_variables_.StudentState.InteractionCount" }
            });

        processBuilder.OnResultFromStep(student)
            .UpdateProcessState(path: "StudentMessages", operation: StateUpdateOperations.Set, value: "_agent_.messages_out")
            .UpdateProcessState(path: "UserMessages", operation: StateUpdateOperations.Increment, value: "_agent_.user_messages")
            .UpdateProcessState(path: "InteractionCount", operation: StateUpdateOperations.Increment, value: "_agent_.student_messages")
            .UpdateProcessState(path: "StudentState.InteractionCount", operation: StateUpdateOperations.Increment, value: "_agent_.student_messages")
            .UpdateProcessState(path: "StudentState.Name", operation: StateUpdateOperations.Set, value: "Runhan")
            .SendEventTo(teacher, messagesIn: ["_variables_.StudentMessages"]);

        processBuilder.OnStepExit(teacher, condition: "contains(to_string(_agent_.messages_out), '[COMPLETE]')")
            .EmitEvent(
                eventName: "correct_answer",
                payload: new Dictionary<string, string>
                {
                    { "Question", "_variables_.TeacherMessages" },
                    { "Answer", "_variables_.StudentMessages" }
                })
            .UpdateProcessState(path: "_variables_.TeacherMessages", operation: StateUpdateOperations.Set, value: "_agent_.messages_out")
            .UpdateProcessState(path: "_variables_.InteractionCount", operation: StateUpdateOperations.Increment, value: 1);

        processBuilder.OnStepExit(teacher, condition: "_default_")
            .SendEventTo(student);

        processBuilder.OnWorkflowEvent("correct_answer")
            .StopProcess(messagesIn: ["_event_.Answer", "_variable_.StudentMessages"]);

        var process = processBuilder.Build();

        await processBuilder.DeployToFoundryAsync(process, TestConfiguration.AzureAI.WorkflowEndpoint);
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
            .WithUserStateInput((state) => state.NextStep.Count() + 1); // TODO: remove

        var plannerStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = ledgerPlannerAgentId, Name = "LedgerPlanner", Type = AzureAIAgentFactory.AzureAIAgentType }, defaultThread: "plan");
        var progressManagerStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = progressManagerAgentId, Name = "ProgressManager", Type = AzureAIAgentFactory.AzureAIAgentType }, defaultThread: "run");
        var routerStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = actionRouterAgentId, Name = "ActionRouter", Type = AzureAIAgentFactory.AzureAIAgentType }, defaultThread: "run");
        var dynamicStep = processBuilder.AddStepFromAgentProxy(stepId: "dynamicAgent", new AgentDefinition { Id = "_variables_.NextAgentId", Name = "DynamicStep", Type = AzureAIAgentFactory.AzureAIAgentType }, threadName: "run");
        var userAgentStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = userAgentId, Name = "UserAgent", Type = AzureAIAgentFactory.AzureAIAgentType }, defaultThread: "run", humanInLoopMode: HITLMode.Always);
        var summarizerStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = summarizerAgentId, Name = "Summarizer", Type = AzureAIAgentFactory.AzureAIAgentType }, defaultThread: "run");
        var factUpdateStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = ledgerFactsUpdateAgentId, Name = "LedgerFactsUpdate", Type = AzureAIAgentFactory.AzureAIAgentType }, defaultThread: "run");
        var planUpdateStep = processBuilder.AddStepFromAgent(new AgentDefinition { Id = ledgerPlannerUpdateAgentId, Name = "LedgerPlannerUpdate", Type = AzureAIAgentFactory.AzureAIAgentType }, defaultThread: "run");

        //Start -> Gaether Facts
        processBuilder.OnInputEvent("start")
            .SendEventTo(new(gatherFactsStep));

        //Gather Facts -> Planner
        processBuilder.OnResultFromStep(gatherFactsStep)
            .UpdateProcessState("Tasks", StateUpdateOperations.Set, "_agent_.outputs.tasks")
            .UpdateProcessState("Facts", StateUpdateOperations.Set, "_agent_.outputs.facts")
            .SendEventTo(plannerStep);

        //Planner -> Progress Manager
        processBuilder.OnResultFromStep(plannerStep)
            .UpdateProcessState("Plan", StateUpdateOperations.Set, "_agent_.outputs.Plan")
            .UpdateProcessState("NextSteps", StateUpdateOperations.Set, "_agent_.outputs.NextStep")
            .SendEventTo(progressManagerStep);

        //Progress Manager -> Router
        processBuilder.OnResultFromStep(progressManagerStep)
            .UpdateProcessState("NextSteps", StateUpdateOperations.Set, "_agent_.outputs")
            .SendEventTo(routerStep);

        //Router -> Progress Manager
        processBuilder.OnResultFromStep(routerStep, condition: "contains(_variables_.NextAgentId, 'UnknownAgent')")
            .UpdateProcessState("NextAgentId", StateUpdateOperations.Set, "_agent_.outputs.targetAgentId")
            .SendEventTo(progressManagerStep, inputs: new Dictionary<string, string> { { "arg1", "_variables_.NextAgentId" } }, messagesIn: ["_variables_.Plan"]);

        //Router -> Facts Update
        processBuilder.OnResultFromStep(routerStep, condition: "contains(_variables_.NextAgentId, 'LedgerFactsUpdate')")
            .SendEventTo(factUpdateStep);

        //Router -> User Agent
        processBuilder.OnResultFromStep(routerStep, condition: "contains(_variables_.NextAgentId, 'UserAgent')")
            .SendEventTo(userAgentStep);

        //Router -> Summarizer
        processBuilder.OnResultFromStep(routerStep, condition: "contains(_variables_.NextAgentId, 'Summarizer')")
            .SendEventTo(summarizerStep);

        //Router -> Dynamic Step
        processBuilder.OnResultFromStep(routerStep, condition: "!contains(_variables_.NextAgentId, 'FinalStepAgent')")
            .SendEventTo(dynamicStep);

        //Dynamic Step -> Progress Manager
        processBuilder.OnResultFromStep(dynamicStep)
            .UpdateProcessState("NextAgentId", StateUpdateOperations.Set, "_agent_.outputs.targetAgentId")
            .SendEventTo(progressManagerStep);

        //Facts Update -> Plan Update
        processBuilder.OnResultFromStep(planUpdateStep);

        //PlanUpdate -> Progress Manager
        processBuilder.OnResultFromStep(progressManagerStep);

        //Summarizer -> End
        processBuilder.OnResultFromStep(summarizerStep).StopProcess();

        var process = processBuilder.Build();
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

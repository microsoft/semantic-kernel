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
        var foundryAgentDefinition1 = new AgentDefinition { Id = "{AGENT_ID}", Name = "Agent1", Type = AzureAIAgentFactory.AzureAIAgentType };
        var foundryAgentDefinition2 = new AgentDefinition { Id = "{AGENT_ID}", Name = "Agent2", Type = AzureAIAgentFactory.AzureAIAgentType };

        var processBuilder = new FoundryProcessBuilder("foundry_agents");

        var agent1 = processBuilder.AddStepFromAgent(foundryAgentDefinition1);
        var agent2 = processBuilder.AddStepFromAgent(foundryAgentDefinition2);

        processBuilder.OnProcessEnter().SendEventTo(agent1);
        processBuilder.OnResultFromStep(agent1).SendEventTo(agent2);
        processBuilder.OnResultFromStep(agent2).StopProcess();

        var process = processBuilder.Build();

        var agentsClient = AzureAIAgent.CreateAgentsClient(TestConfiguration.AzureAI.Endpoint, new AzureCliCredential());

        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddSingleton(agentsClient);
        var kernel = kernelBuilder.Build();

        var context = await process.StartAsync(kernel, new() { Id = "start", Data = "What is the best programming language and why?" });
        var agent1Result = await context.GetStateAsync();

        Assert.NotNull(context);
        Assert.NotNull(agent1Result);
    }

    [Fact]
    public async Task ProcessWithExistingFoundryAgentsAndSharedThreadAsync()
    {
        var foundryAgentDefinition1 = new AgentDefinition { Id = "{AGENT_ID}", Name = "Agent1", Type = AzureAIAgentFactory.AzureAIAgentType };
        var foundryAgentDefinition2 = new AgentDefinition { Id = "{AGENT_ID}", Name = "Agent2", Type = AzureAIAgentFactory.AzureAIAgentType };

        var processBuilder = new FoundryProcessBuilder("foundry_agents");

        processBuilder.AddThread("shared_thread", KernelProcessThreadLifetime.Scoped);

        var agent1 = processBuilder.AddStepFromAgent(foundryAgentDefinition1, defaultThread: "shared_thread");
        var agent2 = processBuilder.AddStepFromAgent(foundryAgentDefinition2, defaultThread: "shared_thread");

        processBuilder.OnProcessEnter().SendEventTo(agent1);
        processBuilder.OnResultFromStep(agent2);
        processBuilder.OnResultFromStep(agent2).StopProcess();

        var process = processBuilder.Build();

        var agentsClient = AzureAIAgent.CreateAgentsClient(TestConfiguration.AzureAI.Endpoint, new AzureCliCredential());

        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddSingleton(agentsClient);
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
        var foundryAgentDefinition1 = new AgentDefinition { Id = "{AGENT_ID}", Name = "Agent1", Type = AzureAIAgentFactory.AzureAIAgentType };
        var foundryAgentDefinition2 = new AgentDefinition { Id = "{AGENT_ID}", Name = "Agent2", Type = AzureAIAgentFactory.AzureAIAgentType };

        // Define the process with a state type
        var processBuilder = new FoundryProcessBuilder<ProcessStateWithCounter>("foundry_agents");
        processBuilder.AddThread("shared_thread", KernelProcessThreadLifetime.Scoped);

        var agent1 = processBuilder.AddStepFromAgent(foundryAgentDefinition1, defaultThread: "shared_thread");
        var agent2 = processBuilder.AddStepFromAgent(foundryAgentDefinition2, defaultThread: "shared_thread");

        processBuilder.OnProcessEnter().SendEventTo(agent1);
        processBuilder.OnResultFromStep(agent1, condition: "_variables_.Counter < `3`").SendEventTo(agent1);
        processBuilder.OnResultFromStep(agent1, condition: "_variables_.Counter >= `3`").SendEventTo(agent2);
        processBuilder.OnResultFromStep(agent2).StopProcess();

        var process = processBuilder.Build();
    }

    [Fact]
    public async Task ProcessWithExistingFoundryAgentsWithProcessStateUpdateAndOrchestrationConditions()
    {
        // Define the agents
        var foundryAgentDefinition1 = new AgentDefinition { Id = "{AGENT_ID}", Name = "Agent1", Type = AzureAIAgentFactory.AzureAIAgentType };
        var foundryAgentDefinition2 = new AgentDefinition { Id = "{AGENT_ID}", Name = "Agent2", Type = AzureAIAgentFactory.AzureAIAgentType };

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
        var foundryAgentDefinition1 = new AgentDefinition { Id = "{AGENT_ID}", Name = "Agent1", Type = AzureAIAgentFactory.AzureAIAgentType };
        var foundryAgentDefinition2 = new AgentDefinition { Id = "_variables_.NextAgentId", Name = "Agent2", Type = AzureAIAgentFactory.AzureAIAgentType };

        // Define the process with a state type
        var processBuilder = new FoundryProcessBuilder<DynamicAgentState>("foundry_agents");
        processBuilder.AddThread("shared_thread", KernelProcessThreadLifetime.Scoped);

        // Agent1 will increment the Counter state variable every time it runs
        var agent1 = processBuilder.AddStepFromAgent(foundryAgentDefinition1, defaultThread: "shared_thread");

        var agent2 = processBuilder.AddStepFromAgentProxy(stepId: "dynamicAgent", foundryAgentDefinition2, threadName: "shared_thread");

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
    public async Task ProcessWithTwoAgentMathChat()
    {
        // Define the agents
        var studentDefinition = new AgentDefinition { Id = "{AGENT_ID}", Name = "Student", Type = AzureAIAgentFactory.AzureAIAgentType };
        var teacherDefinition = new AgentDefinition { Id = "{AGENT_ID2}", Name = "Teacher", Type = AzureAIAgentFactory.AzureAIAgentType };

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

    public class DynamicAgentState
    {
        public string NextAgentId { get; set; } = "{AGENT_ID}";
        public int Counter { get; set; }
    }

    public class ProcessStateWithCounter
    {
        public int Counter { get; set; }
    }
}

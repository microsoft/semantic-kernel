// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using Azure.Identity;
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

    /// <summary>
    /// This example demonstrates how to create a process with two agents that can chat with each other. A student agent and a teacher agent are created.
    /// The process will keep track of the interaction count between the two agents.
    /// </summary>
    [Fact]
    public async Task ProcessWithTwoAgentMathChat()
    {
        // Define the agents. IMPORTANT: replace with your own agent IDs
        var studentDefinition = new AgentDefinition { Id = "{YOUR_STUDENT_AGENT_ID}", Name = "Student", Type = AzureAIAgentFactory.AzureAIAgentType };
        var teacherDefinition = new AgentDefinition { Id = "{YOUR_TEACHER_AGENT_ID}", Name = "Teacher", Type = AzureAIAgentFactory.AzureAIAgentType };

        // Define the process with a state type
        var processBuilder = new FoundryProcessBuilder<TwoAgentMathState>("two_agent_math_chat");

        // Create a thread for the student
        processBuilder.AddThread("Student", KernelProcessThreadLifetime.Scoped);
        processBuilder.AddThread("Teacher", KernelProcessThreadLifetime.Scoped);

        // Add the student
        var student = processBuilder.AddStepFromAgent(studentDefinition);

        // Add the teacher
        var teacher = processBuilder.AddStepFromAgent(teacherDefinition);

        /**************************** Orchestrate ***************************/

        // When the process starts, activate the student agent
        processBuilder.OnProcessEnter().SendEventTo(
            student,
            thread: "_variables_.Student",
            messagesIn: ["_variables_.TeacherMessages"],
            inputs: new Dictionary<string, string>
            {
                { "InteractionCount", "_variables_.StudentState.InteractionCount" }
            });

        // When the student agent exits, update the process state to save the student's messages and update interaction counts
        processBuilder.OnStepExit(student)
            .UpdateProcessState(path: "StudentMessages", operation: StateUpdateOperations.Set, value: "_agent_.messages_out")
            .UpdateProcessState(path: "InteractionCount", operation: StateUpdateOperations.Increment, value: 1)
            .UpdateProcessState(path: "StudentState.InteractionCount", operation: StateUpdateOperations.Increment, value: 1)
            .UpdateProcessState(path: "StudentState.Name", operation: StateUpdateOperations.Set, value: "Runhan");

        // When the student agent is finished, send the messages to the teacher agent
        processBuilder.OnEvent(student, "_default_")
            .SendEventTo(teacher, messagesIn: ["_variables_.StudentMessages"], thread: "Teacher");

        // When the teacher agent exits with a message containing '[COMPLETE]', update the process state to save the teacher's messages and update interaction counts and emit the `correct_answer` event
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

        // When the teacher agent exits with a message not containing '[COMPLETE]', update the process state to save the teacher's messages and update interaction counts
        processBuilder.OnStepExit(teacher, condition: "_default_")
            .UpdateProcessState(path: "_variables_.TeacherMessages", operation: StateUpdateOperations.Set, value: "_agent_.messages_out")
            .UpdateProcessState(path: "_variables_.InteractionCount", operation: StateUpdateOperations.Increment, value: 1);

        // When the teacher agent is finished, send the messages to the student agent
        processBuilder.OnEvent(teacher, "_default_", condition: "_default_")
            .SendEventTo(student, messagesIn: ["_variables_.TeacherMessages"], thread: "Student");

        // When the teacher agent emits the `correct_answer` event, stop the process
        processBuilder.OnEvent(teacher, "correct_answer")
            .StopProcess();

        // Verify that the process can be built and serialized to json
        var processJson = await processBuilder.ToJsonAsync();
        Assert.NotEmpty(processJson);

        var foundryWorkflowId = await processBuilder.DeployToFoundryAsync(TestConfiguration.AzureAI.WorkflowEndpoint);
        Assert.NotEmpty(foundryWorkflowId);
    }

    /// <summary>
    /// Represents the state of the two-agent math chat process.
    /// </summary>
    public class TwoAgentMathState
    {
        public List<ChatMessageContent> StudentMessages { get; set; }

        public List<ChatMessageContent> TeacherMessages { get; set; }

        public StudentState StudentState { get; set; } = new();

        public int InteractionCount { get; set; }
    }

    /// <summary>
    /// Represents the state of the student agent.
    /// </summary>
    public class StudentState
    {
        public int InteractionCount { get; set; }

        public string Name { get; set; }
    }
}

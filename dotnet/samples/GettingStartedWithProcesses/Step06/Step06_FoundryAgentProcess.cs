// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using System.Text;
using Azure.AI.Agents.Persistent;
using Azure.Identity;
using Microsoft.SemanticKernel;
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
        var endpoint = TestConfiguration.AzureAI.Endpoint;
        PersistentAgentsClient client = new(endpoint.TrimEnd('/'), new DefaultAzureCredential(), new PersistentAgentsAdministrationClientOptions().WithPolicy(endpoint, "2025-05-15-preview"));

        Azure.Response<PersistentAgent>? studentAgent = null;
        Azure.Response<PersistentAgent>? teacherAgent = null;

        try
        {
            // Create the single agents
            studentAgent = await client.Administration.CreateAgentAsync(
            model: "gpt-4o",
            name: "Student",
            instructions: "You are a student that answer question from teacher, when teacher gives you question you answer them."
            );

            teacherAgent = await client.Administration.CreateAgentAsync(
                model: "gpt-4o",
                name: "Teacher",
                instructions: "You are a teacher that create pre-school math question for student and check answer.\nIf the answer is correct, you stop the conversation by saying [COMPLETE].\nIf the answer is wrong, you ask student to fix it."
            );

            // Define the process with a state type
            var processBuilder = new FoundryProcessBuilder<TwoAgentMathState>("two_agent_math_chat");

            // Create a thread for the student
            processBuilder.AddThread("Student", KernelProcessThreadLifetime.Scoped);
            processBuilder.AddThread("Teacher", KernelProcessThreadLifetime.Scoped);

            // Add the student
            var student = processBuilder.AddStepFromAgent(studentAgent);

            // Add the teacher
            var teacher = processBuilder.AddStepFromAgent(teacherAgent);

            /**************************** Orchestrate ***************************/

            // When the process starts, activate the student agent
            processBuilder.OnProcessEnter().SendEventTo(
                student,
                thread: "_variables_.Student",
                messagesIn: ["_variables_.TeacherMessages"],
                inputs: new Dictionary<string, string> { });

            // When the student agent exits, update the process state to save the student's messages and update interaction counts
            processBuilder.OnStepExit(student)
                .UpdateProcessState(path: "StudentMessages", operation: StateUpdateOperations.Set, value: "_agent_.messages_out");

            // When the student agent is finished, send the messages to the teacher agent
            processBuilder.OnEvent(student, "_default_")
                .SendEventTo(teacher, messagesIn: ["_variables_.StudentMessages"], thread: "Teacher");

            // When the teacher agent exits with a message containing '[COMPLETE]', update the process state to save the teacher's messages and update interaction counts and emit the `correct_answer` event
            processBuilder.OnStepExit(teacher, condition: "jmespath(contains(to_string(_agent_.messages_out), '[COMPLETE]'))")
                .EmitEvent(
                    eventName: "correct_answer",
                    payload: new Dictionary<string, string>
                    {
                    { "Question", "_variables_.TeacherMessages" },
                    { "Answer", "_variables_.StudentMessages" }
                    })
                .UpdateProcessState(path: "_variables_.TeacherMessages", operation: StateUpdateOperations.Set, value: "_agent_.messages_out");

            // When the teacher agent exits with a message not containing '[COMPLETE]', update the process state to save the teacher's messages and update interaction counts
            processBuilder.OnStepExit(teacher, condition: "_default_")
                .UpdateProcessState(path: "_variables_.TeacherMessages", operation: StateUpdateOperations.Set, value: "_agent_.messages_out");

            // When the teacher agent is finished, send the messages to the student agent
            processBuilder.OnEvent(teacher, "_default_", condition: "_default_")
                .SendEventTo(student, messagesIn: ["_variables_.TeacherMessages"], thread: "Student");

            // When the teacher agent emits the `correct_answer` event, stop the process
            processBuilder.OnEvent(teacher, "correct_answer")
                .StopProcess();

            // Verify that the process can be built and serialized to json
            var processJson = await processBuilder.ToJsonAsync();
            Assert.NotEmpty(processJson);

            var content = await RunWorkflowAsync(client, processBuilder, [new(MessageRole.User, "Go")]);
            Assert.NotEmpty(content);
        }
        finally
        {
            // Clean up the agents
            await client.Administration.DeleteAgentAsync(studentAgent?.Value.Id);
            await client.Administration.DeleteAgentAsync(teacherAgent?.Value.Id);
        }
    }

    private async Task<string> RunWorkflowAsync<T>(PersistentAgentsClient client, FoundryProcessBuilder<T> processBuilder, List<ThreadMessageOptions>? initialMessages = null) where T : class, new()
    {
        Workflow? workflow = null;
        StringBuilder output = new();

        try
        {
            // publish the workflow
            workflow = await client.Administration.Pipeline.PublishWorkflowAsync(processBuilder);

            // threadId is used to store the thread ID
            PersistentAgentThread thread = await client.Threads.CreateThreadAsync(messages: initialMessages ?? []);

            // create run
            await foreach (var run in client.Runs.CreateRunStreamingAsync(thread.Id, workflow.Id))
            {
                if (run is Azure.AI.Agents.Persistent.MessageContentUpdate contentUpdate)
                {
                    output.Append(contentUpdate.Text);
                    Console.Write(contentUpdate.Text);
                }
                else if (run is Azure.AI.Agents.Persistent.RunUpdate runUpdate)
                {
                    if (runUpdate.UpdateKind == Azure.AI.Agents.Persistent.StreamingUpdateReason.RunInProgress && !runUpdate.Value.Id.StartsWith("wf_run", StringComparison.OrdinalIgnoreCase))
                    {
                        Console.WriteLine();
                        Console.Write($"{runUpdate.Value.Metadata["x-agent-name"]}> ");
                    }
                }
            }

            // delete thread, so we can start over
            Console.WriteLine($"\nDeleting thread {thread?.Id}...");
            await client.Threads.DeleteThreadAsync(thread?.Id);
            return output.ToString();
        }
        finally
        {
            // // delete workflow
            Console.WriteLine($"Deleting workflow {workflow?.Id}...");
            await client.Administration.Pipeline.DeleteWorkflowAsync(workflow!);
        }
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

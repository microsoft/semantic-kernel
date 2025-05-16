// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrates how to use the <see cref="GroupChatOrchestration"/>
/// with a group chat manager that uses a chat completion service to
/// control the flow of the conversation.
/// </summary>
public class Step03b_GroupChatWithAIManager(ITestOutputHelper output) : BaseOrchestrationTest(output)
{
    [Fact]
    public async Task GroupChatWithAIManagerAsync()
    {
        // Define the agents
        ChatCompletionAgent farmer =
            this.CreateAgent(
                name: "Farmer",
                description: "A rural farmer from Southeast Asia.",
                instructions:
                """
                You're a farmer from Southeast Asia. 
                Your life is deeply connected to land and family. 
                You value tradition and sustainability. 
                You are in a debate. Feel free to challenge the other participants with respect.
                """);
        ChatCompletionAgent developer =
            this.CreateAgent(
                name: "Developer",
                description: "An urban software developer from the United States.",
                instructions:
                """
                You're a software developer from the United States. 
                Your life is fast-paced and technology-driven. 
                You value innovation, freedom, and work-life balance. 
                You are in a debate. Feel free to challenge the other participants with respect.
                """);
        ChatCompletionAgent teacher =
            this.CreateAgent(
                name: "Teacher",
                description: "A retired history teacher from Eastern Europe",
                instructions:
                """
                You're a retired history teacher from Eastern Europe. 
                You bring historical and philosophical perspectives to discussions. 
                You value legacy, learning, and cultural continuity. 
                You are in a debate. Feel free to challenge the other participants with respect.
                """);
        ChatCompletionAgent activist =
            this.CreateAgent(
                name: "Activist",
                description: "A young activist from South America.",
                instructions:
                """
                You're a young activist from South America. 
                You focus on social justice, environmental rights, and generational change. 
                You are in a debate. Feel free to challenge the other participants with respect.
                """);
        ChatCompletionAgent spiritual =
            this.CreateAgent(
                name: "SpiritualLeader",
                description: "A spiritual leader from the Middle East.",
                instructions:
                """
                You're a spiritual leader from the Middle East. 
                You provide insights grounded in religion, morality, and community service. 
                You are in a debate. Feel free to challenge the other participants with respect.
                """);
        ChatCompletionAgent artist =
            this.CreateAgent(
                name: "Artist",
                description: "An artist from Africa.",
                instructions:
                """
                You're an artist from Africa. 
                You view life through creative expression, storytelling, and collective memory. 
                You are in a debate. Feel free to challenge the other participants with respect.
                """);
        ChatCompletionAgent immigrant =
            this.CreateAgent(
                name: "Immigrant",
                description: "An immigrant entrepreneur from Asia living in Canada.",
                instructions:
                """
                You're an immigrant entrepreneur from Asia living in Canada. 
                You balance trandition with adaption. 
                You focus on family success, risk, and opportunity. 
                You are in a debate. Feel free to challenge the other participants with respect.
                """);
        ChatCompletionAgent doctor =
            this.CreateAgent(
                name: "Doctor",
                description: "A doctor from Scandinavia.",
                instructions:
                """
                You're a doctor from Scandinavia. 
                Your perspective is shaped by public health, equity, and structured societal support. 
                You are in a debate. Feel free to challenge the other participants with respect.
                """);

        // Define the orchestration
        const string topic = "What does a good life mean to you personally?";
        Kernel kernel = this.CreateKernelWithChatCompletion();
        GroupChatOrchestration orchestration =
            new(
                new AIGroupChatManager(
                    topic,
                    kernel.GetRequiredService<IChatCompletionService>())
                {
                    MaximumInvocationCount = 5
                },
                farmer,
                developer,
                teacher,
                activist,
                spiritual,
                artist,
                immigrant,
                doctor)
            {
                LoggerFactory = this.LoggerFactory
            };

        // Start the runtime
        InProcessRuntime runtime = new();
        await runtime.StartAsync();

        // Run the orchestration
        Console.WriteLine($"\n# INPUT: {topic}\n");
        OrchestrationResult<string> result = await orchestration.InvokeAsync(topic, runtime);
        string text = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds * 3));
        Console.WriteLine($"\n# RESULT: {text}");

        await runtime.RunUntilIdleAsync();
    }

    private sealed class AIGroupChatManager(string topic, IChatCompletionService chatCompletion) : GroupChatManager
    {
        private static class Prompts
        {
            public static string Termination(string topic) =>
                $"""
                You are mediator that guides a discussion on the topic of '{topic}'. 
                You need to determine if the discussion has reached a conclusion. 
                If you would like to end the discussion, please respond with True. Otherwise, respond with False.
                """;

            public static string Selection(string topic, string participants) =>
                $"""
                You are mediator that guides a discussion on the topic of '{topic}'. 
                You need to select the next participant to speak. 
                Here are the names and descriptions of the participants: 
                {participants}\n
                Please respond with only the name of the participant you would like to select.
                """;

            public static string Filter(string topic) =>
                $"""
                You are mediator that guides a discussion on the topic of '{topic}'. 
                You have just concluded the discussion. 
                Please summarize the discussion and provide a closing statement.
                """;
        }

        /// <inheritdoc/>
        public override ValueTask<GroupChatManagerResult<string>> FilterResults(ChatHistory history, CancellationToken cancellationToken = default) =>
            this.GetResponseAsync<string>(history, Prompts.Filter(topic), cancellationToken);

        /// <inheritdoc/>
        public override ValueTask<GroupChatManagerResult<string>> SelectNextAgent(ChatHistory history, GroupChatTeam team, CancellationToken cancellationToken = default) =>
            this.GetResponseAsync<string>(history, Prompts.Selection(topic, team.FormatList()), cancellationToken);

        /// <inheritdoc/>
        public override ValueTask<GroupChatManagerResult<bool>> ShouldRequestUserInput(ChatHistory history, CancellationToken cancellationToken = default) =>
            ValueTask.FromResult(new GroupChatManagerResult<bool>(false) { Reason = "The AI group chat manager does not request user input." });

        /// <inheritdoc/>
        public override async ValueTask<GroupChatManagerResult<bool>> ShouldTerminate(ChatHistory history, CancellationToken cancellationToken = default)
        {
            GroupChatManagerResult<bool> result = await base.ShouldTerminate(history, cancellationToken);
            if (!result.Value)
            {
                result = await this.GetResponseAsync<bool>(history, Prompts.Termination(topic), cancellationToken);
            }
            return result;
        }

        private async ValueTask<GroupChatManagerResult<TValue>> GetResponseAsync<TValue>(ChatHistory history, string prompt, CancellationToken cancellationToken = default)
        {
            OpenAIPromptExecutionSettings executionSettings = new() { ResponseFormat = typeof(GroupChatManagerResult<TValue>) };
            ChatHistory request = [.. history, new ChatMessageContent(AuthorRole.System, prompt)];
            ChatMessageContent response = await chatCompletion.GetChatMessageContentAsync(request, executionSettings, kernel: null, cancellationToken);
            string responseText = response.ToString();
            return
                JsonSerializer.Deserialize<GroupChatManagerResult<TValue>>(responseText) ??
                throw new InvalidOperationException($"Failed to parse response: {responseText}");
        }
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Examples;
using Kusto.Cloud.Platform.Utils;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Experimental.Agents;
using Xunit;
using Xunit.Abstractions;

public class Example79_ChatCompletionAgent : BaseTest
{
    /// <summary>
    /// This example demonstrates a chat with the chat completion agent that utilizes the SK ChatCompletion API to communicate with LLM.
    /// </summary>
    [Fact]
    public async Task ChatWithAgentAsync()
    {
        var kernel = Kernel.CreateBuilder()
           .AddAzureOpenAIChatCompletion(
               deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
               endpoint: TestConfiguration.AzureOpenAI.Endpoint,
               apiKey: TestConfiguration.AzureOpenAI.ApiKey,
               modelId: TestConfiguration.AzureOpenAI.ChatModelId)
           .Build();

        var agent = new ChatCompletionAgent(
            kernel,
            instructions: "You act as a professional financial adviser. However, clients may not know the terminology, so please provide a simple explanation.",
            new OpenAIPromptExecutionSettings
            {
                MaxTokens = 500,
                Temperature = 0.7,
                TopP = 1.0,
                PresencePenalty = 0.0,
                FrequencyPenalty = 0.0,
            }
         );

        var prompt = PrintPrompt("I need help with my investment portfolio. Please guide me.");
        PrintConversation(await agent.InvokeAsync(new[] { new ChatMessageContent(AuthorRole.User, prompt) }));
    }

    /// <summary>
    /// This example demonstrates a round-robin chat between two chat completion agents using the TurnBasedChat collaboration experience.
    /// </summary>
    [Fact]
    public async Task TurnBasedAgentsChatAsync()
    {
        var kernel = Kernel.CreateBuilder()
           .AddAzureOpenAIChatCompletion(
               deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
               endpoint: TestConfiguration.AzureOpenAI.Endpoint,
               apiKey: TestConfiguration.AzureOpenAI.ApiKey,
               modelId: TestConfiguration.AzureOpenAI.ChatModelId)
           .Build();

        var settings = new OpenAIPromptExecutionSettings
        {
            MaxTokens = 1500,
            Temperature = 0.7,
            TopP = 1.0,
            PresencePenalty = 0.0,
            FrequencyPenalty = 0.0,
        };

        var fitnessTrainer = new ChatCompletionAgent(
           kernel,
           instructions: "As a fitness trainer, suggest workout routines, and exercises for beginners. " +
           "You are not a stress management expert, so refrain from recommending stress management strategies. " +
           "Collaborate with the stress management expert to create a holistic wellness plan." +
           "Always incorporate stress reduction techniques provided by the stress management expert into the fitness plan." +
           "Always include your role at the beginning of each response, such as 'As a fitness trainer.",
           settings
        );

        var stressManagementExpert = new ChatCompletionAgent(
            kernel,
            instructions: "As a stress management expert, provide guidance on stress reduction strategies. " +
            "Collaborate with the fitness trainer to create a simple and holistic wellness plan." +
            "You are not a fitness expert; therefore, avoid recommending fitness exercises." +
            "If the plan is not aligned with recommended stress reduction plan, ask the fitness trainer to rework it to incorporate recommended stress reduction techniques. " +
            "Only you can stop the conversation by saying WELLNESS_PLAN_COMPLETE if suggested fitness plan is good." +
            "Always include your role at the beginning of each response such as 'As a stress management expert.",
            settings
         );

        var chat = new TurnBasedChat(new[] { fitnessTrainer, stressManagementExpert }, (chatHistory, replies, turn) =>
            turn >= 10 || // Limit the number of turns to 10    
            replies.Any(
                message => message.Role == AuthorRole.Assistant &&
                message.Content!.Contains("WELLNESS_PLAN_COMPLETE", StringComparison.InvariantCulture))); // Exit when the message "WELLNESS_PLAN_COMPLETE" received from agent  

        var prompt = "I need help creating a simple wellness plan for a beginner. Please guide me.";
        PrintConversation(await chat.SendMessageAsync(prompt));
    }

    private string PrintPrompt(string prompt)
    {
        this.WriteLine($"Prompt: {prompt}");

        return prompt;
    }

    private void PrintConversation(IEnumerable<ChatMessageContent> messages)
    {
        foreach (var message in messages)
        {
            this.WriteLine($"------------------------------- {message.Role} ------------------------------");
            this.WriteLine(message.Content);
            this.WriteLine();
        }

        this.WriteLine();
    }

    private sealed class TurnBasedChat
    {
        public TurnBasedChat(IEnumerable<ChatCompletionAgent> agents, Func<ChatHistory, IEnumerable<ChatMessageContent>, int, bool> exitCondition)
        {
            this._agents = agents.ToArray();
            this._exitCondition = exitCondition;
        }

        public async Task<IReadOnlyList<ChatMessageContent>> SendMessageAsync(string message, CancellationToken cancellationToken = default)
        {
            var chat = new ChatHistory();
            chat.AddUserMessage(message);

            IReadOnlyList<ChatMessageContent> result = new List<ChatMessageContent>();

            var turn = 0;

            do
            {
                var agent = this._agents[turn % this._agents.Length];

                result = await agent.InvokeAsync(chat, cancellationToken);

                chat.AddRange(result);

                turn++;
            }
            while (!this._exitCondition(chat, result, turn));

            return chat;
        }

        private readonly ChatCompletionAgent[] _agents;
        private readonly Func<ChatHistory, IEnumerable<ChatMessageContent>, int, bool> _exitCondition;
    }

    public Example79_ChatCompletionAgent(ITestOutputHelper output) : base(output)
    {
    }
}

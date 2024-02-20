// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Kusto.Cloud.Platform.Utils;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Experimental.Agents;
using Pipelines.Sockets.Unofficial.Arenas;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

public class Example79_ChatCompletionAgent : BaseTest
{
    /// <summary>
    /// This example demonstrates a chat with the chat completion agent that utilizes the SK ChatCompletion API to communicate with LLM.
    /// </summary>
    [Fact]
    public async Task ChatWithAgentAsync()
    {
        var agent = new ChatCompletionAgent(
            kernel: this._kernel,
            instructions: "You act as a professional financial adviser. However, clients may not know the terminology, so please provide a simple explanation.",
            description: "Financial Adviser",
            executionSettings: new OpenAIPromptExecutionSettings
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
        var settings = new OpenAIPromptExecutionSettings
        {
            MaxTokens = 1500,
            Temperature = 0.7,
            TopP = 1.0,
            PresencePenalty = 0.0,
            FrequencyPenalty = 0.0,
        };

        var fitnessTrainer = new ChatCompletionAgent(
            kernel: this._kernel,
            instructions: "As a fitness trainer, suggest workout routines, and exercises for beginners. " +
            "You are not a stress management expert, so refrain from recommending stress management strategies. " +
            "Collaborate with the stress management expert to create a holistic wellness plan." +
            "Always incorporate stress reduction techniques provided by the stress management expert into the fitness plan." +
            "Always include your role at the beginning of each response, such as 'As a fitness trainer.",
            description: "Fitness Trainer",
            executionSettings: settings
        );

        var stressManagementExpert = new ChatCompletionAgent(
            kernel: this._kernel,
            instructions: "As a stress management expert, provide guidance on stress reduction strategies. " +
            "Collaborate with the fitness trainer to create a simple and holistic wellness plan." +
            "You are not a fitness expert; therefore, avoid recommending fitness exercises." +
            "If the plan is not aligned with recommended stress reduction plan, ask the fitness trainer to rework it to incorporate recommended stress reduction techniques. " +
            "Only you can stop the conversation by saying WELLNESS_PLAN_COMPLETE if suggested fitness plan is good." +
            "Always include your role at the beginning of each response such as 'As a stress management expert.",
            description: "Stress Management Expert",
            executionSettings: settings
         );

        var chat = new TurnBasedChat(new[] { fitnessTrainer, stressManagementExpert }, (chatHistory, replies, turn) =>
            turn >= 10 || // Limit the number of turns to 10    
            replies.Any(
                message => message.Role == AuthorRole.Assistant &&
                message.Items.OfType<TextContent>().Any(c => c.Text!.Contains("WELLNESS_PLAN_COMPLETE", StringComparison.InvariantCulture)))); // Exit when the message "WELLNESS_PLAN_COMPLETE" received from agent  

        var prompt = "I need help creating a simple wellness plan for a beginner. Please guide me.";
        PrintConversation(await chat.SendMessageAsync(prompt));
    }

    /// <summary>
    /// This example demonstrates the auto function invocation capability of the chat completion agent.
    /// </summary>
    [Fact]
    public async Task AgentAutoFunctionInvocationAsync()
    {
        this._kernel.Plugins.AddFromType<CRM>();

        var settings = new OpenAIPromptExecutionSettings
        {
            MaxTokens = 1500,
            Temperature = 0.7,
            TopP = 1.0,
            PresencePenalty = 0.0,
            FrequencyPenalty = 0.0,
            ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions
        };

        var agent = new ChatCompletionAgent(
            kernel: this._kernel,
            instructions: "As a fitness trainer, suggest workout routines, and exercises for beginners.",
            description: "Fitness Trainer",
            executionSettings: settings);

        var prompt = PrintPrompt("I need help creating a simple wellness plan for my client James that is appropriate for his age. Please guide me.");
        PrintConversation(await agent.InvokeAsync(new[] { new ChatMessageContent(AuthorRole.User, prompt) }));
    }

    /// <summary>
    /// This example demonstrates the manual function invocation capability of the chat completion agent.
    /// </summary>
    [Fact]
    public async Task AgentManualFunctionInvocationAsync()
    {
        this._kernel.Plugins.AddFromType<CRM>();

        var settings = new OpenAIPromptExecutionSettings
        {
            MaxTokens = 1500,
            Temperature = 0.7,
            TopP = 1.0,
            PresencePenalty = 0.0,
            FrequencyPenalty = 0.0,
            ToolCallBehavior = ToolCallBehavior.EnableKernelFunctions,
            ResultsPerPrompt = 1
        };

        KernelAgent agent = new ChatCompletionAgent(
            kernel: this._kernel,
            instructions: "As a fitness trainer, suggest workout routines, and exercises for beginners.",
            description: "Fitness Trainer",
            executionSettings: settings);

        // Register a post-processor to handle the agent's response to manually invoke the CRM function.
        agent = new AgentDecorator(agent, postProcessor: async messages =>
        {
            var message = messages.Single();

            if (message is not OpenAIChatMessageContent openAIChatMessageContent)
            {
                return messages;
            }

            var toolCalls = openAIChatMessageContent.ToolCalls.OfType<ChatCompletionsFunctionToolCall>().ToList();
            if (toolCalls.Count == 0)
            {
                return messages;
            }

            var result = new List<ChatMessageContent>(messages); // The original tool calling "request" from LLM is already included in the messages list.

            if (message.Source is not KernelAgent agent)
            {
                throw new KernelException("The kernel agent is not available in the message metadata.");
            }

            foreach (var toolCall in toolCalls)
            {
                string content = "Unable to find function. Please try again!";

                if (agent.Kernel.Plugins.TryGetFunctionAndArguments(toolCall, out KernelFunction? function, out KernelArguments? arguments))
                {
                    var functionResult = await function.InvokeAsync(agent.Kernel, arguments);

                    // A custom logic can be added here that would interpret the function's result, update the agent's message, remove it, or replace it with a different one.

                    content = JsonSerializer.Serialize(functionResult.GetValue<object>());
                }

                result.Add(new ChatMessageContent(
                    AuthorRole.Tool,
                    content,
                    metadata: new Dictionary<string, object?>(1) { { OpenAIChatMessageContent.ToolIdProperty, toolCall.Id } }));
            }

            return result;
        });

        var prompt = PrintPrompt("I need help creating a simple wellness plan for my client James that is appropriate for his age. Please guide me.");
        PrintConversation(await agent.InvokeAsync(new[] { new ChatMessageContent(AuthorRole.User, prompt) }));
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

            foreach (var etxContent in message.Items.OfType<TextContent>())
            {
                this.WriteLine(etxContent.Text);
            }

            this.WriteLine();
            this.WriteLine();
        }

        this.WriteLine();
    }

    /// <summary>
    /// The turn-based chat. For demonstration purposes only.
    /// </summary>
    private sealed class TurnBasedChat
    {
        public TurnBasedChat(IEnumerable<KernelAgent> agents, Func<IReadOnlyList<ChatMessageContent>, IEnumerable<ChatMessageContent>, int, bool> exitPredicate)
        {
            this._agents = agents.ToArray();
            this._exitCondition = exitPredicate;
        }

        public async Task<IReadOnlyList<ChatMessageContent>> SendMessageAsync(string message, CancellationToken cancellationToken = default)
        {
            var chat = new List<ChatMessageContent>();
            chat.Add(new ChatMessageContent(AuthorRole.User, message));

            IReadOnlyList<ChatMessageContent> result = new List<ChatMessageContent>();

            var turn = 0;

            do
            {
                var agent = this._agents[turn % this._agents.Length];

                result = await agent.InvokeAsync(chat, cancellationToken: cancellationToken);

                chat.AddRange(result);

                turn++;
            }
            while (!this._exitCondition(chat, result, turn));

            return chat;
        }

        private readonly KernelAgent[] _agents;
        private readonly Func<IReadOnlyList<ChatMessageContent>, IEnumerable<ChatMessageContent>, int, bool> _exitCondition;
    }

    /// <summary>
    /// The agent decorator for pre/post-processing agent messages. This is for demonstration purposes only.
    /// </summary>
    private sealed class AgentDecorator : KernelAgent
    {
        private readonly Func<IReadOnlyList<ChatMessageContent>, Task<IReadOnlyList<ChatMessageContent>>>? _preProcessor;
        private readonly Func<IReadOnlyList<ChatMessageContent>, Task<IReadOnlyList<ChatMessageContent>>>? _postProcessor;
        private readonly KernelAgent _agent;

        public AgentDecorator(
            KernelAgent agent,
            Func<IReadOnlyList<ChatMessageContent>, Task<IReadOnlyList<ChatMessageContent>>>? preProcessor = null,
            Func<IReadOnlyList<ChatMessageContent>, Task<IReadOnlyList<ChatMessageContent>>>? postProcessor = null) : base(agent.Kernel, agent.Description)
        {
            this._agent = agent;
            this._preProcessor = preProcessor;
            this._postProcessor = postProcessor;
        }

        public override async Task<IReadOnlyList<ChatMessageContent>> InvokeAsync(IReadOnlyList<ChatMessageContent> messages, PromptExecutionSettings? executionSettings = null, CancellationToken cancellationToken = default)
        {
            if (this._preProcessor != null)
            {
                messages = await this._preProcessor(messages);
            }

            var result = await this._agent.InvokeAsync(messages, executionSettings, cancellationToken);

            if (this._postProcessor != null)
            {
                result = await this._postProcessor(result);
            }

            return result;
        }
    }

    private sealed class CRM
    {
        [KernelFunction, Description("Returns client details")]
        public static ClientDetails GetClientDetails(string name)
        {
            return name switch
            {
                "James" => new ClientDetails { Name = name, Age = 60 },
                _ => throw new NotSupportedException($"Unknown client '{name}'."),
            };
        }
    }

    private sealed class ClientDetails
    {
        public string Name { get; set; }

        public byte Age { get; set; }
    }

    public Example79_ChatCompletionAgent(ITestOutputHelper output) : base(output)
    {
        this._kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion("gpt-4-1106-preview", TestConfiguration.OpenAI.ApiKey)
            .Build();
    }

    private readonly Kernel _kernel;
}

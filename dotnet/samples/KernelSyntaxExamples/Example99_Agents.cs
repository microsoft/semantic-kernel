// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Experimental.Agents;
using Microsoft.SemanticKernel.Experimental.Agents.Agents;
using Microsoft.SemanticKernel.Experimental.Agents.Strategy;
using Plugins;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// Showcase Agent abstraction and patterns.
/// </summary>
public class Example99_Agents : BaseTest
{
    /// <summary>
    /// Demonstrate single chat agent.
    /// </summary>
    [Fact]
    public async Task RunChatSingleAgentAsync()
    {
        WriteLine("======== Run:Single Chat Agent ========");

        var agent =
            CreateChatAgent(
                "Parrot",
                "Repeat the user message in the voice of a pirate and then end with a parrot sound.");

        await RunSingleAgentAsync(agent);
    }

    /// <summary>
    /// Demonstrate single chat agent.
    /// </summary>
    [Fact]
    public async Task RunChatDualAgentsAsync()
    {
        WriteLine("======== Run:Dual Chat Agents ========");

        var agent1 = CreateChatAgent("Optimistic", "Respond with optimism.");
        var agent2 = CreateChatAgent("Pessimistic", "Respond with extreme skeptism...don't be polite.");

        await RunDualAgentAsync(agent1, agent2, "I think I'm going to do something really important today!");
    }

    /// <summary>
    /// Demonstrate tooled chat agent.
    /// </summary>
    [Fact]
    public async Task RunChatToolsAgentAsync()
    {
        WriteLine("======== Run:Tooled Chat Agent ========");

        var plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        var agent =
            CreateChatAgent(
                "Host",
                "Use tools to answer questions about menu.",
                plugin);

        await RunToolAgentAsync(agent);
    }

    /// <summary>
    /// Demonstrate single gpt agent.
    /// </summary>
    [Fact]
    public async Task RunGptSingleAgentAsync()
    {
        WriteLine("======== Run:Single GPT Agent ========");

        var agent =
            await CreateGptAgentAsync(
                "Parrot",
                "Repeat the user message in the voice of a pirate and then end with a parrot sound.");

        await RunSingleAgentAsync(agent);
    }

    /// <summary>
    /// Demonstrate single gpt agent.
    /// </summary>
    [Fact]
    public async Task RunGptDualAgentsAsync()
    {
        WriteLine("======== Run:Dual GPT Agents ========");

        var agent1 = await CreateGptAgentAsync("Optimistic", "Evaluate the user input with optimism.");
        var agent2 = await CreateGptAgentAsync("Pessimistic", "Respond with extreme skeptism...don't be polite.");

        await RunDualAgentAsync(agent1, agent2, "I think I'm going to do something really important today!");
    }

    /// <summary>
    /// Demonstrate tooled gpt agent.
    /// </summary>
    [Fact]
    public async Task RunGptToolsAgentAsync()
    {
        WriteLine("======== Run:Tooled GPT Agent ========");

        var plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        var agent =
            await CreateGptAgentAsync(
                "Host",
                "Use tools to answer questions about menu.",
                plugin);

        await RunToolAgentAsync(agent);
    }

    /// <summary>
    /// Demonstrate tooled gpt agent.
    /// </summary>
    [Fact]
    public async Task RunGptCodeAgentAsync()
    {
        WriteLine("======== Run:Coding GPT Agent ========");

        var agent =
            await CreateGptAgentAsync(
                "Coder",
                enableCoding: true);

        await ChatAsync(
            agent,
            "What is the solution to `3x + 2 = 14`?",
            "What is the fibinacci sequence until 101?");
    }

    /// <summary>
    /// Demonstrate retrieval gpt agent.
    /// </summary>
    [Fact]
    public async Task RunGptRetrievalAgentAsync()
    {
        WriteLine("======== Run:Retrieval GPT Agent ========");

        // $$$ FILEID

        var agent =
            await CreateGptAgentAsync(
                "Helper",
                enableRetrieval: true);

        await ChatAsync(
            agent,
            "Where did sam go?",
            "When does the flight leave Seattle?",
            "What is the hotel contact info at the destination?");
    }

    /// <summary>
    /// Demonstrate chart maker gpt agent.
    /// </summary>
    [Fact]
    public async Task RunGptChartAgentAsync()
    {
        WriteLine("======== Run:Charting GPT Agent ========");

        var agent =
            await CreateGptAgentAsync(
                "ChartMaker",
                "Create charts as requested without explanation.",
                enableCoding: true);

        await ChatAsync(
            agent,
            @"
            Display this data using a bar-chart:

            Banding  Brown Pink Yellow  Sum
            X00000   339   433     126  898
            X00300    48   421     222  691
            X12345    16   395     352  763
            Others    23   373     156  552
            Sum      426  1622     856 2904
            ",
            "Can you regenerate this same chart using the category names as the bar colors?");
    }

    /// <summary>
    /// Demonstrate mixed agents.
    /// </summary>
    [Fact]
    public async Task RunMixedDualAgentAsync()
    {
        WriteLine("======== Run:Mixed Agents ========");

        var agent1 = CreateChatAgent("Optimistic", "Respond with optimism.");
        var agent2 = await CreateGptAgentAsync("Pessimistic", "Respond with extreme skeptism...don't be polite.");

        await RunDualAgentAsync(agent1, agent2, "I think I'm going to do something really important today!");
    }

    /// <summary>
    /// Demonstrate strategy nexus with mixed agents.
    /// </summary>
    [Fact]
    public async Task RunMixedAgentExpressionStrategyAsync()
    {
        WriteLine("======== Run:Agents in ExpressionStrategy Nexus ========");

        var agent1 = CreateChatAgent("Optimistic", "Respond with optimism.");
        var agent2 = await CreateGptAgentAsync("Pessimistic", "Respond with extreme skeptism...don't be polite.");

        await RunStrategyAsync(
            "I think I'm going to do something really important today!",
            new NexusExecutionSettings
            {
                MaximumIterations = 6,
                CompletionCriteria = new ExpressionCompletionStrategy("really"), // Terminate on pessimistic phrase.
            },
            agent1,
            agent2);
    }

    /// <summary>
    /// Demonstrate semantic completion strategy with mixed agents.
    /// </summary>
    [Fact]
    public async Task RunMixedAgentCompletionStrategyAsync()
    {
        WriteLine("======== Run:Agents in CompletionStrategy Nexus ========");

        var agent1 = CreateChatAgent("CopyWriter", "You are a copywriter with ten years of experience and are known for brevity and a dry humor. You're laser focused on the goal at hand. Don't waste time with chit chat. The goal is to refine and decide on the single best copy as an expert in the field.  Consider suggestions when refining an idea.");
        var agent2 = await CreateGptAgentAsync("ArtDirector", "You are an art director who has opinions about copywriting born of a love for David Ogilvy. The goal is to determine is the given copy is acceptable to print.  If not, provide insight on how to refine suggested copy without example.");

        await RunStrategyAsync(
            "concept: maps made out of egg cartons.",
            new NexusExecutionSettings
            {
                CompletionCriteria =
                    new SemanticCompletionStrategy(
                        agent1.Kernel.GetRequiredService<IChatCompletionService>(),
                        "Respond with only true or false in evaulation on whether ArtDirector has given approval"),
            },
            agent1,
            agent2);
    }

    /// <summary>
    /// Demonstrate semantic completion strategy with mixed agents.
    /// </summary>
    [Fact]
    public async Task RunMixedAgentSelectionStrategyAsync() // $$$ IMPROVE / BROKE
    {
        WriteLine("======== Run:Agents in SelectionStrategy Nexus ========");

        var agent1 = CreateChatAgent("Player1", "Your name is Player1. You are playing a game taking turns with other players.  Only respond with your own turn.  On your first turn, only introduce yourself by name.  Then on subsequent turns, play the game. The game starts when one player states they've thought of a number from 1 to 10.  The other players take turns guessing what the number is.  The player who knows the number replies with: too low, too high, or you got it.");
        var agent2 = CreateChatAgent("Player2", "Your name is Player2. You are playing a game taking turns with other players.  Only respond with your own turn.  On your first turn, only introduce yourself by name.  Then on subsequent turns, play the game. The game starts when one player states they've thought of a number from 1 to 10.  The other players take turns guessing what the number is.  The player who knows the number replies with: too low, too high, or you got it.");
        var agent3 = CreateChatAgent("Player3", "Your name is Player3. You are playing a game taking turns with other players.  Only respond with your own turn.  On your first turn, only introduce yourself by name.  Then on subsequent turns, play the game. The game starts when one player states they've thought of a number from 1 to 10.  The other players take turns guessing what the number is.  The player who knows the number replies with: too low, too high, or you got it.");

        await RunStrategyAsync(
            input: null,
            new NexusExecutionSettings
            {
                MaximumIterations = 9,
                CompletionCriteria =
                    new SemanticCompletionStrategy(
                        agent1.Kernel.GetRequiredService<IChatCompletionService>(),
                        "Someone correctly guesses the number."),
                SelectionStrategy =
                    new SemanticSelectionStrategy(
                        agent1.Kernel.GetRequiredService<IChatCompletionService>(),
                        "Your job is to only state the name of the player whose turn is next without explanation.  You are not a player.  There are three player: Player1, Player2, and Player3.  Pick anyone to start.  Only respond with the player name.  Players start by taking turns to introduce themselves. After all players has introduced themselves, one player thinks of a number from 1 to 10.  The other players take turns guessing what the number is.  The player who knows the number replies with: too low, too high, or you got it.",
                        new OpenAIPromptExecutionSettings
                        {
                            Temperature = 0,
                        })
            },
            agent1,
            agent2,
            agent3);
    }

    /// <summary>
    /// Demonstrate single chat agent.
    /// </summary>
    [Fact]
    public async Task RunChatNexusAgentsAsync()
    {
        WriteLine("======== Run:Nexus Agent ========");

        var agent1 = CreateChatAgent("Optimistic", "Respond with optimism.");
        var agent2 = CreateChatAgent("Pessimistic", "Respond with extreme skeptism...don't be polite.");
        var agent3 = CreateChatAgent("Summarizer", "Summarize the conversation.");
        var nexus = new AgentChat(agent1, agent2)
        {
            ExecutionSettings = new()
            {
                SelectionStrategy = new SequentialSelectionStrategy(),
                MaximumIterations = 4,
            }
        };
        var agentX = new NexusAgent(nexus);

        var chat = new AgentChat();
        await ChatAsync(chat, agentX, "I think I'm going to do something really important today!");
        await ChatAsync(chat, agent3);
    }

    private async Task RunSingleAgentAsync(KernelAgent agent)
    {
        await ChatAsync(
            agent,
            "Fortune favors the bold.",
            "I came, I saw, I conquered.",
            "Practice makes perfect.");
    }

    private async Task RunToolAgentAsync(KernelAgent agent)
    {
        await ChatAsync(
            agent,
            "What is the special soup?",
            "What is the special drink?",
            "How much for a soup and a drink?",
            "What else is available?");
    }

    private async Task RunDualAgentAsync(KernelAgent agent1, KernelAgent agent2, string input)
    {
        this.WriteLine("[TEST]");
        WriteAgent(agent1);
        WriteAgent(agent2);

        var nexus = new AgentChat();

        await ChatAsync(nexus, agent1, input);
        await ChatAsync(nexus, agent2);

        await WriteHistoryAsync(nexus);
        await WriteHistoryAsync(nexus, agent1);
        await WriteHistoryAsync(nexus, agent2);
    }

    private async Task RunStrategyAsync(
        string? input,
        NexusExecutionSettings settings,
        params KernelAgent[] agents)
    {
        settings.SelectionStrategy ??= new SequentialSelectionStrategy();

        this.WriteLine("[TEST]");
        foreach (var agent in agents)
        {
            WriteAgent(agent);
        }

        var nexus = new AgentChat(agents) { ExecutionSettings = settings };

        await WriteContentAsync(nexus.InvokeAsync(input));

        await WriteHistoryAsync(nexus);
        foreach (var agent in agents)
        {
            await WriteHistoryAsync(nexus, agent);
        }
    }

    /// <summary>
    /// Common chat loop.
    /// </summary>
    private async Task<AgentNexus> ChatAsync(
        Agent agent,
        params string[] messages)
    {
        this.WriteLine("[TEST]");
        WriteAgent(agent);

        var nexus = new AgentChat();

        // Process each user message and agent response.
        foreach (var message in messages)
        {
            await ChatAsync(nexus, agent, message);
        }

        await WriteHistoryAsync(nexus);
        await WriteHistoryAsync(nexus, agent);

        return nexus;
    }

    private Task ChatAsync(AgentChat nexus, Agent agent, string? message = null)
    {
        return WriteContentAsync(nexus.InvokeAsync(agent, message));
    }

    private string GetApiKey()
    {
        if (string.IsNullOrEmpty(TestConfiguration.AzureOpenAI.Endpoint))
        {
            return TestConfiguration.OpenAI.ApiKey;
        }

        return TestConfiguration.AzureOpenAI.ApiKey;
    }

    private void WriteAgent(Agent agent)
    {
        this.WriteLine($"[{agent.GetType().Name}:{agent.Id}:{agent.Name ?? "*"}]");
    }

    private async Task WriteContentAsync(IAsyncEnumerable<ChatMessageContent> messages)
    {
        await foreach (var content in messages)
        {
            this.WriteLine($"# {content.Role} - {content.Name ?? "*"}: '{content.Content}'");
        }
    }
    private Task WriteHistoryAsync(AgentNexus nexus, Agent? agent = null)
    {
        if (agent == null)
        {
            this.WriteLine("\n[primary history]");
        }
        else
        {
            this.WriteLine();
            this.WriteAgent(agent);
        }

        return WriteContentAsync(nexus.GetHistoryAsync(agent));
    }

    private async Task<GptAgent> CreateGptAgentAsync(
        string name,
        string? instructions = null,
        KernelPlugin? plugin = null,
        bool enableCoding = false,
        bool enableRetrieval = false)
    {
        return
            await GptAgent.CreateAsync(
                CreateKernel(plugin),
                GetApiKey(),
                instructions,
                description: null,
                name,
                enableCoding,
                enableRetrieval);
    }

    private ChatAgent CreateChatAgent(
        string name,
        string? instructions = null,
        KernelPlugin? plugin = null)
    {
        return
            new ChatAgent(
                CreateKernel(plugin),
                instructions,
                description: null,
                name,
                new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions });
    }

    private Kernel CreateKernel(KernelPlugin? plugin = null)
    {
        var builder = Kernel.CreateBuilder();

        if (string.IsNullOrEmpty(TestConfiguration.AzureOpenAI.Endpoint))
        {
            builder.AddOpenAIChatCompletion(
                TestConfiguration.OpenAI.ChatModelId,
                TestConfiguration.OpenAI.ApiKey);
        }
        else
        {
            builder.AddAzureOpenAIChatCompletion(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey);
        }

        if (plugin != null)
        {
            builder.Plugins.Add(plugin);
        }

        return builder.Build();
    }

    public Example99_Agents(ITestOutputHelper output) : base(output)
    {
    }
}

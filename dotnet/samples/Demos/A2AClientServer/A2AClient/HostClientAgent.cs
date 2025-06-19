// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.A2A;
using SharpA2A.Core;

namespace A2A;

internal sealed class HostClientAgent
{
    internal HostClientAgent(ILogger logger)
    {
        this._logger = logger;
    }
    internal async Task InitializeAgentAsync(string modelId, string apiKey, string[] agentUrls)
    {
        try
        {
            this._logger.LogInformation("Initializing Semantic Kernel agent with model: {ModelId}", modelId);

            // Connect to the remote agents via A2A
            var createAgentTasks = agentUrls.Select(agentUrl => this.CreateAgentAsync(agentUrl));
            var agents = await Task.WhenAll(createAgentTasks);
            var agentFunctions = agents.Select(agent => AgentKernelFunctionFactory.CreateFromAgent(agent)).ToList();
            var agentPlugin = KernelPluginFactory.CreateFromFunctions("AgentPlugin", agentFunctions);

            // Define the Host agent
            var builder = Kernel.CreateBuilder();
            builder.AddOpenAIChatCompletion(modelId, apiKey);
            builder.Plugins.Add(agentPlugin);
            var kernel = builder.Build();
            kernel.FunctionInvocationFilters.Add(new ConsoleOutputFunctionInvocationFilter());

            this.Agent = new ChatCompletionAgent()
            {
                Kernel = kernel,
                Name = "HostClient",
                Instructions =
                    """
                    You specialize in handling queries for users and using your tools to provide answers.
                    """,
                Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
            };
        }
        catch (Exception ex)
        {
            this._logger.LogError(ex, "Failed to initialize HostClientAgent");
            throw;
        }
    }

    /// <summary>
    /// The associated <see cref="Agent"/>
    /// </summary>
    public Agent? Agent { get; private set; }

    #region private
    private readonly ILogger _logger;

    private async Task<A2AAgent> CreateAgentAsync(string agentUri)
    {
        var httpClient = new HttpClient
        {
            BaseAddress = new Uri(agentUri),
            Timeout = TimeSpan.FromSeconds(60)
        };

        var client = new A2AClient(httpClient);
        var cardResolver = new A2ACardResolver(httpClient);
        var agentCard = await cardResolver.GetAgentCardAsync();

        return new A2AAgent(client, agentCard!);
    }
    #endregion
}

internal sealed class ConsoleOutputFunctionInvocationFilter() : IFunctionInvocationFilter
{
    private static string IndentMultilineString(string multilineText, int indentLevel = 1, int spacesPerIndent = 4)
    {
        // Create the indentation string
        var indentation = new string(' ', indentLevel * spacesPerIndent);

        // Split the text into lines, add indentation, and rejoin
        char[] NewLineChars = { '\r', '\n' };
        string[] lines = multilineText.Split(NewLineChars, StringSplitOptions.None);

        return string.Join(Environment.NewLine, lines.Select(line => indentation + line));
    }
    public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
    {
        Console.ForegroundColor = ConsoleColor.DarkGray;

        Console.WriteLine($"\nCalling Agent {context.Function.Name} with arguments:");
        Console.ForegroundColor = ConsoleColor.Gray;

        foreach (var kvp in context.Arguments)
        {
            Console.WriteLine(IndentMultilineString($"  {kvp.Key}: {kvp.Value}"));
        }

        await next(context);

        if (context.Result.GetValue<object>() is ChatMessageContent[] chatMessages)
        {
            Console.ForegroundColor = ConsoleColor.DarkGray;

            Console.WriteLine($"Response from Agent {context.Function.Name}:");
            foreach (var message in chatMessages)
            {
                Console.ForegroundColor = ConsoleColor.Gray;

                Console.WriteLine(IndentMultilineString($"{message}"));
            }
        }
        Console.ResetColor();
    }
}

// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.A2A;
using SharpA2A.Core;

namespace A2A;

internal class HostClientAgent
{
    internal HostClientAgent(ILogger logger)
    {
        this._logger = logger;
    }
    internal async Task InitializeAgentAsync(string modelId, string apiKey, string baseAddress)
    {
        try
        {
            this._logger.LogInformation("Initializing Semantic Kernel agent with model: {ModelId}", modelId);

            // Connect to the remote agents via A2A
            var agentPlugin = KernelPluginFactory.CreateFromFunctions("AgentPlugin",
            [
                AgentKernelFunctionFactory.CreateFromAgent(await this.CreateAgentAsync($"{baseAddress}/currency/")),
                AgentKernelFunctionFactory.CreateFromAgent(await this.CreateAgentAsync($"{baseAddress}/invoice/"))
            ]);

            // Define the TravelPlannerAgent
            var builder = Kernel.CreateBuilder();
            builder.AddOpenAIChatCompletion(modelId, apiKey);
            builder.Plugins.Add(agentPlugin);
            var kernel = builder.Build();

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
            BaseAddress = new Uri(agentUri)
        };

        var client = new A2AClient(httpClient);
        var cardResolver = new A2ACardResolver(httpClient);
        var agentCard = await cardResolver.GetAgentCardAsync();

        return new A2AAgent(client, agentCard);
    }
    #endregion
}

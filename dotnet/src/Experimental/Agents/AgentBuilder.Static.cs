// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Agents.Internal;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Context for interacting with OpenAI REST API.
/// </summary>
public partial class AgentBuilder
{
    /// <summary>
    /// Create a new agent.
    /// </summary>
    /// <param name="apiKey">The OpenAI API key</param>
    /// <param name="model">The agent chat model (required)</param>
    /// <param name="instructions">The agent instructions (required)</param>
    /// <param name="name">The agent name (optional)</param>
    /// <param name="description">The agent description(optional)</param>
    /// <returns>The requested <see cref="IAgent">.</see></returns>
    public static async Task<IAgent> NewAsync(
        string apiKey,
        string model,
        string instructions,
        string? name = null,
        string? description = null)
    {
        return
            await new AgentBuilder()
                .WithOpenAIChatCompletion(model, apiKey)
                .WithInstructions(instructions)
                .WithName(name)
                .WithDescription(description)
                .BuildAsync().ConfigureAwait(false);
    }

    /// <summary>
    /// Retrieve an existing agent, by identifier.
    /// </summary>
    /// <param name="apiKey">A context for accessing OpenAI REST endpoint</param>
    /// <param name="agentId">The agent identifier</param>
    /// <param name="plugins">Plugins to initialize as agent tools</param>
    /// <param name="cancellationToken">A cancellation token</param>
    /// <returns>An initialized <see cref="Agent"> instance.</see></returns>
    public static async Task<IAgent> GetAgentAsync(
        string apiKey,
        string agentId,
        IEnumerable<KernelPlugin>? plugins = null,
        CancellationToken cancellationToken = default)
    {
        var restContext = new OpenAIRestContext(apiKey);
        var resultModel = await restContext.GetAssistantModelAsync(agentId, cancellationToken).ConfigureAwait(false);

        return new Agent(resultModel, null, restContext, plugins);
    }
}

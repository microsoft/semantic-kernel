// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Extension methods for <see cref="AgentFactory"/> to create agents from YAML.
/// </summary>
public static class YamlAgentFactoryExtensions
{
    /// <summary>
    /// Create a <see cref="Agent"/> from the given YAML text.
    /// </summary>
    /// <param name="kernelAgentFactory">Kernel agent factory which will be used to create the agent.</param>
    /// <param name="text">Text string containing the YAML representation of a kernel agent.</param>
    /// <param name="options">Optional <see cref="AgentCreationOptions"/> instance.</param>
    /// <param name="configuration">Optional <see cref="IConfiguration"/> instance.</param>
    /// <param name="cancellationToken">Optional cancellation token</param>
    public static async Task<Agent?> CreateAgentFromYamlAsync(this AgentFactory kernelAgentFactory, string text, AgentCreationOptions? options = null, IConfiguration? configuration = null, CancellationToken cancellationToken = default)
    {
        var agentDefinition = AgentDefinitionYaml.FromYaml(text, configuration);
        agentDefinition.Type ??= (kernelAgentFactory.Types.Count > 0 ? kernelAgentFactory.Types[0] : null);

        return await kernelAgentFactory.CreateAsync(
            options?.Kernel ?? new Kernel(),
            agentDefinition,
            options,
            cancellationToken).ConfigureAwait(false);
    }
}

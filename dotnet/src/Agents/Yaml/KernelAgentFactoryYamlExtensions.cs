// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Extension methods for <see cref="KernelAgentFactory"/> to create agents from YAML.
/// </summary>
public static class KernelAgentFactoryYamlExtensions
{
    /// <summary>
    /// Create a <see cref="KernelAgent"/> from the given YAML text.
    /// </summary>
    /// <param name="kernelAgentFactory">Kernel agent factory which will be used to create the agent.</param>
    /// <param name="kernel">Kernel instance.</param>
    /// <param name="text">Text string containing the YAML representation of a kernel agent.</param>
    /// <param name="cancellationToken">Optional cancellation token.</param>
    public static async Task<KernelAgent?> CreateAgentFromYamlAsync(this KernelAgentFactory kernelAgentFactory, Kernel kernel, string text, CancellationToken cancellationToken = default)
    {
        var agentDefinition = AgentDefinitionYaml.FromYaml(text);
        agentDefinition.Type = agentDefinition.Type ?? (kernelAgentFactory.Types.Count > 0 ? kernelAgentFactory.Types[0] : null);

        return await kernelAgentFactory.CreateAsync(
            kernel,
            agentDefinition,
            cancellationToken).ConfigureAwait(false);
    }
}

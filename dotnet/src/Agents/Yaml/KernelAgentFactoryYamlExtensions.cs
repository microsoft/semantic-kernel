// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
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
    /// <param name="kernelAgentFactory"></param>
    /// <param name="kernel"></param>
    /// <param name="text"></param>
    /// <param name="cancellationToken"></param>
    public static async Task<KernelAgent?> CreateAgentFromYamlAsync(this KernelAgentFactory kernelAgentFactory, Kernel kernel, string text, CancellationToken cancellationToken = default)
    {
        var agentDefinition = AgentDefinitionYaml.FromYaml(text);
        agentDefinition.Type = agentDefinition.Type ?? kernelAgentFactory.Types.FirstOrDefault();

        return await kernelAgentFactory.CreateAsync(
            kernel,
            agentDefinition,
            cancellationToken).ConfigureAwait(false);
    }
}

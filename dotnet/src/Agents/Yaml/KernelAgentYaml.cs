// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Factory;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Factory methods for creating <seealso cref="KernelAgent"/> instances.
/// </summary>
public static class KernelAgentYaml
{
    /// <summary>
    /// Create a <see cref="KernelAgent"/> from the given YAML text.
    /// </summary>
    /// <param name="kernel"></param>
    /// <param name="text"></param>
    /// <param name="kernelAgentFactory"></param>
    /// <param name="cancellationToken"></param>
    public static async Task<KernelAgent?> FromAgentYamlAsync(Kernel kernel, string text, IKernelAgentFactory kernelAgentFactory, CancellationToken cancellationToken = default)
    {
        var agentDefinition = ToAgentDefinition(text);

        return await kernelAgentFactory.CreateAsync(
            kernel,
            agentDefinition,
            cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Convert the given YAML text to a <see cref="AgentDefinition"/> model.
    /// </summary>
    /// <param name="text">YAML representation of the <see cref="AgentDefinition"/> to use to create the prompt function.</param>
    public static AgentDefinition ToAgentDefinition(string text)
    {
        var deserializer = new DeserializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .WithTypeConverter(new PromptExecutionSettingsTypeConverter())
            .Build();

        return deserializer.Deserialize<AgentDefinition>(text);
    }
}

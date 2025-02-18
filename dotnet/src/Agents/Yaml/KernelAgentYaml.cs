// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Factory methods for creating <seealso cref="KernelAgent"/> instances.
/// </summary>
public static class KernelAgentYaml
{
    public static KernelAgent FromAgentYaml(
        string text,
        ILoggerFactory? loggerFactory = null)
    {
        var agentDefinition = ToAgentDefinition(text);

        return KernelAgentFactory.CreateFromDefinition(
            agentDefinition,
            loggerFactory);
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

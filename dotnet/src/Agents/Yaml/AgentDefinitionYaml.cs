// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Helper methods for creating <see cref="AgentDefinition"/> from YAML.
/// </summary>
[Experimental("SKEXP0110")]
public static class AgentDefinitionYaml
{
    /// <summary>
    /// Convert the given YAML text to a <see cref="AgentDefinition"/> model.
    /// </summary>
    /// <param name="text">YAML representation of the <see cref="AgentDefinition"/> to use to create the prompt function.</param>
    public static AgentDefinition FromYaml(string text)
    {
        var deserializer = new DeserializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .WithTypeConverter(new ModelConfigurationTypeConverter())
            .WithTypeConverter(new AgentMetadataTypeConverter())
            .Build();

        var agentDefinition = deserializer.Deserialize<AgentDefinition>(text);
        return agentDefinition.UpdateInputNames();
    }

    #region private
    /// <summary>
    /// Update the input names to match dictionary keys in this <see cref="AgentDefinition"/> instance.
    /// </summary>
    /// <param name="agentDefinition">AgentDefinition instance to update.</param>
    private static AgentDefinition UpdateInputNames(this AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);

        if (agentDefinition?.Inputs is not null)
        {
            foreach (var keyValuePair in agentDefinition.Inputs)
            {
                keyValuePair.Value.Name = keyValuePair.Key;
            }
        }

        return agentDefinition!;
    }
    #endregion
}

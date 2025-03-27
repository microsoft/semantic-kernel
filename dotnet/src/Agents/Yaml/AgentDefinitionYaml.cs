// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Configuration;
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
    /// <param name="configuration">Optional instance of <see cref="IConfiguration"/> which can provide configuration settings.</param>
    public static AgentDefinition FromYaml(string text, IConfiguration? configuration = null)
    {
        var deserializer = new DeserializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .WithTypeConverter(new ModelConfigurationTypeConverter())
            .WithTypeConverter(new AgentMetadataTypeConverter())
            .Build();

        var agentDefinition = deserializer.Deserialize<AgentDefinition>(text);
        return Normalize(agentDefinition, configuration);
    }

    #region private
    /// <summary>
    /// Update the input names to match dictionary keys in this <see cref="AgentDefinition"/> instance.
    /// </summary>
    /// <param name="agentDefinition">AgentDefinition instance to update.</param>
    /// <param name="configuration">Optional instance of <see cref="IConfiguration"/> which can provide configuration settings.</param>
    private static AgentDefinition Normalize(AgentDefinition agentDefinition, IConfiguration? configuration)
    {
        Verify.NotNull(agentDefinition);

        if (agentDefinition?.Inputs is not null)
        {
            foreach (var keyValuePair in agentDefinition.Inputs)
            {
                keyValuePair.Value.Name = keyValuePair.Key;
            }
        }

        if (configuration is not null)
        {
            agentDefinition!.Normalize(configuration);
        }

        return agentDefinition!;
    }
    #endregion
}

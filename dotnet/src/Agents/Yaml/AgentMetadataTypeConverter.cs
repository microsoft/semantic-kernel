// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using YamlDotNet.Core;
using YamlDotNet.Core.Events;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Type converter custom deserialization for <see cref="AgentMetadata"/> from YAML.
/// </summary>
/// <remarks>
/// Required to correctly deserialize the <see cref="AgentDefinition.Metadata"/> from YAML.
/// </remarks>
internal sealed class AgentMetadataTypeConverter : IYamlTypeConverter
{
    /// <inheritdoc/>
    public bool Accepts(Type type)
    {
        return type == typeof(AgentMetadata);
    }

    /// <inheritdoc/>
    public object? ReadYaml(IParser parser, Type type)
    {
        s_deserializer ??= new DeserializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .IgnoreUnmatchedProperties() // Required to ignore the 'type' property used as type discrimination. Otherwise, the "Property 'type' not found on type '{type.FullName}'" exception is thrown.
            .Build();

        parser.MoveNext(); // Move to the first property  

        var agentMetadata = new AgentMetadata();
        while (parser.Current is not MappingEnd)
        {
            var propertyName = parser.Consume<Scalar>().Value;
            switch (propertyName)
            {
                case "authors":
                    agentMetadata.Authors = s_deserializer.Deserialize<List<string>>(parser);
                    break;
                case "tags":
                    agentMetadata.Tags = s_deserializer.Deserialize<List<string>>(parser);
                    break;
                default:
                    (agentMetadata.ExtensionData ??= new Dictionary<string, object?>()).Add(propertyName, s_deserializer.Deserialize<object>(parser));
                    break;
            }
        }
        parser.MoveNext(); // Move past the MappingEnd event  
        return agentMetadata;
    }

    /// <inheritdoc/>
    public void WriteYaml(IEmitter emitter, object? value, Type type)
    {
        throw new NotImplementedException();
    }

    /// <summary>
    /// The YamlDotNet deserializer instance.
    /// </summary>
    private static IDeserializer? s_deserializer;
}

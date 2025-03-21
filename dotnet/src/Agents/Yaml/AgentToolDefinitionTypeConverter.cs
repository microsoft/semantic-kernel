// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using YamlDotNet.Core;
using YamlDotNet.Core.Events;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Type converter custom deserialization for <see cref="AgentToolDefinition"/> from YAML.
/// </summary>
/// <remarks>
/// Required to correctly deserialize the <see cref="AgentToolDefinition.Options"/> from YAML.
/// </remarks>
internal sealed class AgentToolDefinitionTypeConverter : IYamlTypeConverter
{
    /// <inheritdoc/>
    public bool Accepts(Type type)
    {
        return type == typeof(AgentToolDefinition);
    }

    /// <inheritdoc/>
    public object? ReadYaml(IParser parser, Type type)
    {
        s_deserializer ??= new DeserializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .IgnoreUnmatchedProperties() // Required to ignore the 'type' property used as type discrimination. Otherwise, the "Property 'type' not found on type '{type.FullName}'" exception is thrown.
            .Build();

        parser.MoveNext(); // Move to the first property  

        var agentToolDefinition = new AgentToolDefinition();
        while (parser.Current is not MappingEnd)
        {
            var propertyName = parser.Consume<Scalar>().Value;
            switch (propertyName)
            {
                case "type":
                    agentToolDefinition.Type = s_deserializer.Deserialize<string>(parser);
                    break;
                case "name":
                    agentToolDefinition.Id = s_deserializer.Deserialize<string>(parser);
                    break;
                case "description":
                    agentToolDefinition.Description = s_deserializer.Deserialize<string>(parser);
                    break;
                default:
                    (agentToolDefinition.Options ??= new Dictionary<string, object?>()).Add(propertyName, s_deserializer.Deserialize<object>(parser));
                    break;
            }
        }
        parser.MoveNext(); // Move past the MappingEnd event  
        return agentToolDefinition;
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

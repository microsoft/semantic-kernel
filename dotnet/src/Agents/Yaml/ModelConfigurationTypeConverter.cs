// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using YamlDotNet.Core;
using YamlDotNet.Core.Events;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Type converter with custom deserialization for <see cref="ModelConnection"/> from YAML.
/// </summary>
///  <remarks>
/// Required to correctly deserialize the <see cref="ModelConnection.ExtensionData"/> from YAML.
/// </remarks>
internal sealed class ModelConfigurationTypeConverter : IYamlTypeConverter
{
    /// <inheritdoc/>
    public bool Accepts(Type type)
    {
        return type == typeof(ModelConnection);
    }

    /// <inheritdoc/>
    public object? ReadYaml(IParser parser, Type type)
    {
        s_deserializer ??= new DeserializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .IgnoreUnmatchedProperties() // Required to ignore the 'type' property used as type discrimination. Otherwise, the "Property 'type' not found on type '{type.FullName}'" exception is thrown.
            .Build();

        parser.MoveNext(); // Move to the first property  

        var modelConfiguration = new ModelConnection();
        while (parser.Current is not MappingEnd)
        {
            var propertyName = parser.Consume<Scalar>().Value;
            switch (propertyName)
            {
                case "type":
                    modelConfiguration.Type = s_deserializer.Deserialize<string>(parser);
                    break;
                case "service_id":
                    modelConfiguration.ServiceId = s_deserializer.Deserialize<string>(parser);
                    break;
                default:
                    (modelConfiguration.ExtensionData ??= new Dictionary<string, object?>()).Add(propertyName, s_deserializer.Deserialize<object>(parser));
                    break;
            }
        }
        parser.MoveNext(); // Move past the MappingEnd event  
        return modelConfiguration;
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

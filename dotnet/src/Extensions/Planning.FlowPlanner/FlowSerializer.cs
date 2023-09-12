// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Planning.Flow;

using System.IO;
using System.Text.Json;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

/// <summary>
/// Serializer for <see cref="Flow"/>
/// </summary>
public static class FlowSerializer
{
    /// <summary>
    /// Deserialize flow from yaml
    /// </summary>
    /// <param name="yaml">the yaml string</param>
    /// <returns>the <see cref="Flow"/> instance</returns>
    public static Flow DeserializeFromYaml(string yaml)
    {
        var deserializer = new DeserializerBuilder()
            .WithNamingConvention(CamelCaseNamingConvention.Instance)
            .Build();

        var flow = deserializer.Deserialize<Flow>(new StringReader(yaml));

        return flow;
    }

    /// <summary>
    /// Deserialize flow from json
    /// </summary>
    /// <param name="json">the json string</param>
    /// <returns>the <see cref="Flow"/> instance</returns>
    public static Flow? DeserializeFromJson(string json)
    {
        var options = new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true,
            Converters = { new JsonStringEnumConverter(JsonNamingPolicy.CamelCase) }
        };

        return JsonSerializer.Deserialize<Flow>(json, options);
    }
}

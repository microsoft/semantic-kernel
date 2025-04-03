// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Helper class for serializing and deserializing workflows
/// </summary>
public static class WorkflowSerializer
{
    /// <summary>
    /// Deserializes a workflow from YAML
    /// </summary>
    /// <param name="yaml">The YAML string</param>
    /// <returns>The deserialized workflow</returns>
    public static Workflow DeserializeFromYaml(string yaml)
    {
        try
        {
            var deserializer = new DeserializerBuilder()
                .WithNamingConvention(UnderscoredNamingConvention.Instance)
                .IgnoreUnmatchedProperties()
                .Build();

            var wrapper = deserializer.Deserialize<WorkflowWrapper>(yaml);
            return wrapper?.Workflow;
        }
        catch (System.Exception ex)
        {
            throw;
        }
    }

    /// <summary>
    /// Deserializes a workflow from a YAML file
    /// </summary>
    /// <param name="filePath">Path to the YAML file</param>
    /// <returns>The deserialized workflow</returns>
    public static async Task<Workflow> DeserializeFromYamlFileAsync(string filePath)
    {
        using var reader = new StreamReader(filePath);
        var yaml = await reader.ReadToEndAsync().ConfigureAwait(false);
        return DeserializeFromYaml(yaml);
    }

    /// <summary>
    /// Serializes a workflow to YAML
    /// </summary>
    /// <param name="workflow">The workflow to serialize</param>
    /// <returns>The YAML string</returns>
    public static string SerializeToYaml(Workflow workflow)
    {
        var serializer = new SerializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .ConfigureDefaultValuesHandling(DefaultValuesHandling.OmitNull | DefaultValuesHandling.OmitEmptyCollections)
            .Build();

        return serializer.Serialize(workflow);
    }

    /// <summary>
    /// Serializes a workflow to a YAML file
    /// </summary>
    /// <param name="workflow">The workflow to serialize</param>
    /// <param name="filePath">Path to the YAML file</param>
    public static async Task SerializeToYamlFileAsync(Workflow workflow, string filePath)
    {
        var yaml = SerializeToYaml(workflow);
        using var writer = new StreamWriter(filePath);
        await writer.WriteAsync(yaml).ConfigureAwait(false);
    }

    /// <summary>
    /// Deserializes a workflow from JSON
    /// </summary>
    /// <param name="json">The JSON string</param>
    /// <returns>The deserialized workflow</returns>
    public static Workflow DeserializeFromJson(string json)
    {
        var options = new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
            PropertyNameCaseInsensitive = true
        };

        return JsonSerializer.Deserialize<Workflow>(json, options)!;
    }

    /// <summary>
    /// Deserializes a workflow from a JSON file
    /// </summary>
    /// <param name="filePath">Path to the JSON file</param>
    /// <returns>The deserialized workflow</returns>
    public static async Task<Workflow> DeserializeFromJsonFileAsync(string filePath)
    {
        using var reader = new StreamReader(filePath);
        var json = await reader.ReadToEndAsync().ConfigureAwait(false);
        return DeserializeFromJson(json);
    }

    /// <summary>
    /// Serializes a workflow to JSON
    /// </summary>
    /// <param name="workflow">The workflow to serialize</param>
    /// <returns>The JSON string</returns>
    public static string SerializeToJson(Workflow workflow)
    {
        var options = new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
            WriteIndented = true
        };

        return JsonSerializer.Serialize(workflow, options);
    }

    /// <summary>
    /// Serializes a workflow to a JSON file
    /// </summary>
    /// <param name="workflow">The workflow to serialize</param>
    /// <param name="filePath">Path to the JSON file</param>
    public static async Task SerializeToJsonFileAsync(Workflow workflow, string filePath)
    {
        var json = SerializeToJson(workflow);
        using var writer = new StreamWriter(filePath);
        await writer.WriteAsync(json).ConfigureAwait(false);
    }
}

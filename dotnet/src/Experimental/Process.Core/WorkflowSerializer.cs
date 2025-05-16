// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.Serialization;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using YamlDotNet.Core;
using YamlDotNet.Core.Events;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Helper class for serializing and deserializing workflows
/// </summary>
internal static class WorkflowSerializer
{
    private static readonly JsonSerializerOptions s_jsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        PropertyNameCaseInsensitive = true,
        Converters = { new JsonEnumMemberStringEnumConverter(JsonNamingPolicy.SnakeCaseLower) }
    };

    /// <summary>
    /// Deserializes a workflow from YAML
    /// </summary>
    /// <param name="yaml">The YAML string</param>
    /// <returns>The deserialized workflow</returns>
    public static Workflow DeserializeFromYaml(string yaml)
    {
        var deserializer = new DeserializerBuilder()
                .WithNamingConvention(UnderscoredNamingConvention.Instance)
                .IgnoreUnmatchedProperties()
                .Build();

        Workflow? workflow = null;

        try
        {
            // Try to deserialize workflow wrapper version first.
            var wrapper = deserializer.Deserialize<WorkflowWrapper>(yaml);
            workflow = wrapper?.Workflow;
        }
#pragma warning disable CA1031 // Do not catch general exception types
        catch
#pragma warning restore CA1031 // Do not catch general exception types
        {
            // If it's not a workflow wrapper version, continue with parsing non-wrapper version.
        }

        if (workflow is null)
        {
            workflow = deserializer.Deserialize<Workflow>(yaml);
        }

        return workflow;
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
            .WithTypeConverter(new SnakeCaseEnumConverter())
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
        return JsonSerializer.Deserialize<Workflow>(json, s_jsonOptions)!;
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
        return JsonSerializer.Serialize(workflow, s_jsonOptions);
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

    internal class SnakeCaseEnumConverter : IYamlTypeConverter
    {
        public bool Accepts(Type type) => type.IsEnum;

        public object ReadYaml(IParser parser, Type type)
        {
            var value = parser.Consume<Scalar>().Value;
            return Enum.Parse(type, value.Replace("_", ""), true);
        }

        public void WriteYaml(IEmitter emitter, object? value, Type type)
        {
            var enumValue = value?.ToString();
            if (enumValue == null)
            {
                return;
            }

#pragma warning disable CA1308 // Normalize strings to uppercase
            var snakeCaseValue = string.Concat(enumValue.Select((x, i) =>
                i > 0 && char.IsUpper(x) ? "_" + x : x.ToString())).ToLowerInvariant();
#pragma warning restore CA1308 // Normalize strings to uppercase
            emitter.Emit(new Scalar(snakeCaseValue));
        }
    }

    internal class JsonEnumMemberStringEnumConverter : JsonConverterFactory
    {
        private readonly JsonNamingPolicy? _namingPolicy;
        private readonly bool _allowIntegerValues;
        private readonly JsonStringEnumConverter _baseConverter;

        public JsonEnumMemberStringEnumConverter() : this(null, true) { }

        public JsonEnumMemberStringEnumConverter(JsonNamingPolicy? namingPolicy = null, bool allowIntegerValues = true)
        {
            this._namingPolicy = namingPolicy;
            this._allowIntegerValues = allowIntegerValues;
            this._baseConverter = new JsonStringEnumConverter(namingPolicy, allowIntegerValues);
        }

        public override bool CanConvert(Type typeToConvert) => this._baseConverter.CanConvert(typeToConvert);

        public override JsonConverter CreateConverter(Type typeToConvert, JsonSerializerOptions options)
        {
            var query = from field in typeToConvert.GetFields(BindingFlags.Public | BindingFlags.Static)
                        let attr = field.GetCustomAttribute<EnumMemberAttribute>()
                        where attr != null && attr.Value != null
                        select (field.Name, attr.Value);
            var dictionary = query.ToDictionary(p => p.Item1, p => p.Item2);
            if (dictionary.Count > 0)
            {
                return new JsonStringEnumConverter(new DictionaryLookupNamingPolicy(dictionary, this._namingPolicy), this._allowIntegerValues).CreateConverter(typeToConvert, options);
            }

            return this._baseConverter.CreateConverter(typeToConvert, options);
        }
    }

    internal class JsonNamingPolicyDecorator : JsonNamingPolicy
    {
        private readonly JsonNamingPolicy? _underlyingNamingPolicy;

        public JsonNamingPolicyDecorator(JsonNamingPolicy? underlyingNamingPolicy) => this._underlyingNamingPolicy = underlyingNamingPolicy;
        public override string ConvertName(string name) => this._underlyingNamingPolicy?.ConvertName(name) ?? name;
    }

    internal class DictionaryLookupNamingPolicy : JsonNamingPolicyDecorator
    {
        private readonly Dictionary<string, string> _dictionary;

        public DictionaryLookupNamingPolicy(Dictionary<string, string> dictionary, JsonNamingPolicy? underlyingNamingPolicy) : base(underlyingNamingPolicy) => this._dictionary = dictionary ?? throw new KernelException("Failed to serialize Enum Name");
        public override string ConvertName(string name) => this._dictionary.TryGetValue(name, out var value) ? value : base.ConvertName(name);
    }
}

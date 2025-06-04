// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

/// <summary>
/// A function to be used in the chat completion request.
/// </summary>
internal sealed partial class MistralFunction
{
    /// <summary>
    /// The name of the function to be called.Must be a-z,A-Z,0-9 or contain underscores and dashes, with a maximum length of 64.
    /// </summary>
    [JsonPropertyName("name")]
    public string Name { get; set; }

    /// <summary>
    /// The description of the function to help the model determine when and how to invoke it.
    /// </summary>
    [JsonPropertyName("description")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Description { get; set; }

    /// <summary>
    /// The function parameters, defined using a JSON Schema object. If omitted, the function is considered to have an empty parameter list.
    /// </summary>
    [JsonPropertyName("parameters")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public MistralParameters? Parameters { get; set; }

    /// <summary>
    /// The arguments provided by the model to call the function.
    /// </summary>
    [JsonPropertyName("arguments")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Arguments { get; set; }

    /// <summary>Gets the separator used between the plugin name and the function name, if a plugin name is present.</summary>
    public static char NameSeparator { get; set; } = '-';

    /// <summary>Gets the name of the plugin with which the function is associated, if any.</summary>
    [JsonIgnore]
    public string? PluginName { get; }

    /// <summary>Gets the name of the function.</summary>
    [JsonIgnore]
    public string FunctionName { get; }

    /// <summary>
    /// Construct an instance of <see cref="MistralFunction"/>.
    /// </summary>
    [JsonConstructorAttribute]
    public MistralFunction(string name, string description, MistralParameters? parameters)
    {
        ValidFunctionName(name);

        var parts = name.Split(NameSeparator);

        this.Name = name;
        this.PluginName = (parts.Length == 1) ? null : parts[0];
        this.FunctionName = (parts.Length == 1) ? parts[0] : parts[1];
        this.Description = description;
        this.Parameters = parameters;
    }

    /// <summary>
    /// Construct an instance of <see cref="MistralFunction"/>.
    /// </summary>
    public MistralFunction(KernelFunctionMetadata metadata)
    {
        var name = string.IsNullOrEmpty(metadata.PluginName) ? metadata.Name : $"{metadata.PluginName}{NameSeparator}{metadata.Name}";
        ValidFunctionName(name);

        this.Name = name;
        this.PluginName = metadata.PluginName;
        this.FunctionName = metadata.Name;
        this.Description = metadata.Description;
        this.Parameters = ToMistralParameters(metadata);
    }

    /// <summary>
    /// Construct an instance of <see cref="MistralFunction"/>.
    /// </summary>
    public MistralFunction(string functionName, string? pluginName)
    {
        var name = string.IsNullOrEmpty(pluginName) ? functionName : $"{pluginName}{NameSeparator}{functionName}";
        ValidFunctionName(name);

        this.Name = name;
        this.PluginName = pluginName;
        this.FunctionName = functionName;
    }

    #region private

#if NET
    [GeneratedRegex("^[0-9A-Za-z_-]*$")]
    private static partial Regex AsciiLettersDigitsUnderscoresRegex();
#else
    private static Regex AsciiLettersDigitsUnderscoresRegex() => s_asciiLettersDigitsUnderscoresRegex;
    private static readonly Regex s_asciiLettersDigitsUnderscoresRegex = new("^[0-9A-Za-z_-]*$");
#endif

    private static void ValidFunctionName(string name)
    {
        Verify.NotNull(name, nameof(name));
        Verify.True(name.Length <= 64, "The name of the function must be less than or equal to 64 characters.", nameof(name));

        if (!AsciiLettersDigitsUnderscoresRegex().IsMatch(name))
        {
            throw new ArgumentException($"A function name can contain only ASCII letters, digits, dashes and underscores: '{name}' is not a valid name.");
        }
    }

    private static MistralParameters ToMistralParameters(KernelFunctionMetadata metadata)
    {
        var parameters = new MistralParameters();

        if (metadata.Parameters is { Count: > 0 })
        {
            foreach (var parameter in metadata.Parameters)
            {
                parameters.Properties.Add(parameter.Name, parameter.Schema ?? GetDefaultSchemaForTypelessParameter(parameter.Description));
                if (parameter.IsRequired)
                {
                    parameters.Required.Add(parameter.Name);
                }
            }
        }

        return parameters;
    }

    /// <summary>Gets a <see cref="KernelJsonSchema"/> for a typeless parameter with the specified description, defaulting to typeof(string)</summary>
    private static KernelJsonSchema GetDefaultSchemaForTypelessParameter(string? description)
    {
        // If there's a description, incorporate it.
        if (!string.IsNullOrWhiteSpace(description))
        {
            return KernelJsonSchemaBuilder.Build(typeof(string), description);
        }

        // Otherwise, we can use a cached schema for a string with no description.
        return s_stringNoDescriptionSchema;
    }

    /// <summary>
    /// Cached schema for a string without a description.
    /// </summary>
    private static readonly KernelJsonSchema s_stringNoDescriptionSchema = KernelJsonSchema.Parse("{\"type\":\"string\"}");

    #endregion
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.AI;
using OpenAI.Chat;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Represents a function parameter that can be passed to an OpenAI function tool call.
/// </summary>
public sealed class OpenAIFunctionParameter
{
    internal OpenAIFunctionParameter(string? name, string? description, bool isRequired, Type? parameterType, KernelJsonSchema? schema)
    {
        this.Name = name ?? string.Empty;
        this.Description = description ?? string.Empty;
        this.IsRequired = isRequired;
        this.ParameterType = parameterType;
        this.Schema = schema;
    }

    /// <summary>Gets the name of the parameter.</summary>
    public string Name { get; }

    /// <summary>Gets a description of the parameter.</summary>
    public string Description { get; }

    /// <summary>Gets whether the parameter is required vs optional.</summary>
    public bool IsRequired { get; }

    /// <summary>Gets the <see cref="Type"/> of the parameter, if known.</summary>
    public Type? ParameterType { get; }

    /// <summary>Gets a JSON schema for the parameter, if known.</summary>
    public KernelJsonSchema? Schema { get; }
}

/// <summary>
/// Represents a function return parameter that can be returned by a tool call to OpenAI.
/// </summary>
public sealed class OpenAIFunctionReturnParameter
{
    internal OpenAIFunctionReturnParameter(string? description, Type? parameterType, KernelJsonSchema? schema)
    {
        this.Description = description ?? string.Empty;
        this.Schema = schema;
        this.ParameterType = parameterType;
    }

    /// <summary>Gets a description of the return parameter.</summary>
    public string Description { get; }

    /// <summary>Gets the <see cref="Type"/> of the return parameter, if known.</summary>
    public Type? ParameterType { get; }

    /// <summary>Gets a JSON schema for the return parameter, if known.</summary>
    public KernelJsonSchema? Schema { get; }
}

/// <summary>
/// Represents a function that can be passed to the OpenAI API
/// </summary>
public sealed class OpenAIFunction
{
    /// <summary>
    /// Cached <see cref="BinaryData"/> storing the JSON for a function with no parameters.
    /// </summary>
    /// <remarks>
    /// This is an optimization to avoid serializing the same JSON Schema over and over again
    /// for this relatively common case.
    /// </remarks>
    private static readonly BinaryData s_zeroFunctionParametersSchema = new("""{"type":"object","required":[],"properties":{}}""");
    /// <summary>
    /// Same as above, but with additionalProperties: false for strict mode.
    /// </summary>
    private static readonly BinaryData s_zeroFunctionParametersSchema_strict = new("""{"type":"object","required":[],"properties":{},"additionalProperties":false}""");
    /// <summary>
    /// Cached schema for a descriptionless string.
    /// </summary>
    private static readonly KernelJsonSchema s_stringNoDescriptionSchema = KernelJsonSchema.Parse("""{"type":"string"}""");
    /// <summary>
    /// Cached schema for a descriptionless string that's nullable.
    /// </summary>
    private static readonly KernelJsonSchema s_stringNoDescriptionSchemaAndNull = KernelJsonSchema.Parse("""{"type":["string","null"]}""");

    /// <summary>Initializes the OpenAIFunction.</summary>
    internal OpenAIFunction(
        string? pluginName,
        string functionName,
        string? description,
        IReadOnlyList<OpenAIFunctionParameter>? parameters,
        OpenAIFunctionReturnParameter? returnParameter)
    {
        Verify.NotNullOrWhiteSpace(functionName);

        this.PluginName = pluginName;
        this.FunctionName = functionName;
        this.Description = description;
        this.Parameters = parameters;
        this.ReturnParameter = returnParameter;
    }

    /// <summary>Gets the separator used between the plugin name and the function name, if a plugin name is present.</summary>
    /// <remarks>This separator was previously <c>_</c>, but has been changed to <c>-</c> to better align to the behavior elsewhere in SK and in response
    /// to developers who want to use underscores in their function or plugin names. We plan to make this setting configurable in the future.</remarks>
    public static string NameSeparator { get; set; } = "-";

    /// <summary>Gets the name of the plugin with which the function is associated, if any.</summary>
    public string? PluginName { get; }

    /// <summary>Gets the name of the function.</summary>
    public string FunctionName { get; }

    /// <summary>Gets the fully-qualified name of the function.</summary>
    /// <remarks>
    /// This is the concatenation of the <see cref="PluginName"/> and the <see cref="FunctionName"/>,
    /// separated by <see cref="NameSeparator"/>. If there is no <see cref="PluginName"/>, this is
    /// the same as <see cref="FunctionName"/>.
    /// </remarks>
    public string FullyQualifiedName =>
        string.IsNullOrEmpty(this.PluginName) ? this.FunctionName : $"{this.PluginName}{NameSeparator}{this.FunctionName}";

    /// <summary>Gets a description of the function.</summary>
    public string? Description { get; }

    /// <summary>Gets a list of parameters to the function, if any.</summary>
    public IReadOnlyList<OpenAIFunctionParameter>? Parameters { get; }

    /// <summary>Gets the return parameter of the function, if any.</summary>
    public OpenAIFunctionReturnParameter? ReturnParameter { get; }

    /// <summary>
    /// Converts the <see cref="OpenAIFunction"/> representation to the OpenAI SDK's
    /// <see cref="ChatTool"/> representation.
    /// </summary>
    /// <returns>A <see cref="ChatTool"/> containing all the function information.</returns>
    [Obsolete("Use the overload that takes a boolean parameter instead.")]
    public ChatTool ToFunctionDefinition() => this.ToFunctionDefinition(false);

    /// <summary>
    /// Converts the <see cref="OpenAIFunction"/> representation to the OpenAI SDK's
    /// <see cref="ChatTool"/> representation.
    /// </summary>
    /// <returns>A <see cref="ChatTool"/> containing all the function information.</returns>
    public ChatTool ToFunctionDefinition(bool allowStrictSchemaAdherence)
    {
        BinaryData resultParameters = allowStrictSchemaAdherence ? s_zeroFunctionParametersSchema_strict : s_zeroFunctionParametersSchema;

        IReadOnlyList<OpenAIFunctionParameter>? parameters = this.Parameters;
        if (parameters is { Count: > 0 })
        {
            var properties = new Dictionary<string, KernelJsonSchema>();
            var required = new List<string>();

            foreach (var parameter in parameters)
            {
                var parameterSchema = (parameter.Schema, allowStrictSchemaAdherence) switch
                {
                    (not null, true) => GetSanitizedSchemaForStrictMode(parameter.Schema, !parameter.IsRequired && allowStrictSchemaAdherence),
                    (not null, false) => parameter.Schema,
                    (null, _) => GetDefaultSchemaForTypelessParameter(parameter.Description, allowStrictSchemaAdherence),
                };
                properties.Add(parameter.Name, parameterSchema);
                if (parameter.IsRequired || allowStrictSchemaAdherence)
                {
                    required.Add(parameter.Name);
                }
            }

            resultParameters = allowStrictSchemaAdherence
                ? BinaryData.FromObjectAsJson(new
                {
                    type = "object",
                    required,
                    properties,
                    additionalProperties = false
                })
                : BinaryData.FromObjectAsJson(new
                {
                    type = "object",
                    required,
                    properties,
                });
        }

        return ChatTool.CreateFunctionTool
        (
            functionName: this.FullyQualifiedName,
            functionDescription: this.Description,
            functionParameters: resultParameters,
            functionSchemaIsStrict: allowStrictSchemaAdherence
        );
    }

    /// <summary>Gets a <see cref="KernelJsonSchema"/> for a typeless parameter with the specified description, defaulting to typeof(string)</summary>
    private static KernelJsonSchema GetDefaultSchemaForTypelessParameter(string? description, bool allowStrictSchemaAdherence)
    {
        // If there's a description, incorporate it.
        if (!string.IsNullOrWhiteSpace(description))
        {
            return allowStrictSchemaAdherence ?
                GetOptionalStringSchemaWithDescription(description!) :
                KernelJsonSchemaBuilder.Build(typeof(string), description, AIJsonSchemaCreateOptions.Default);
        }

        // Otherwise, we can use a cached schema for a string with no description.
        return allowStrictSchemaAdherence ? s_stringNoDescriptionSchemaAndNull : s_stringNoDescriptionSchema;
    }

    private static KernelJsonSchema GetOptionalStringSchemaWithDescription(string description)
    {
        var jObject = new JsonObject
        {
            { "description", description },
            { "type", new JsonArray { "string", "null" } },
        };
        return KernelJsonSchema.Parse(jObject.ToString());
    }
    private static KernelJsonSchema GetSanitizedSchemaForStrictMode(KernelJsonSchema schema, bool insertNullType)
    {
        var forbiddenPropertyNames = s_forbiddenKeywords.Where(k => schema.RootElement.TryGetProperty(k, out _)).ToArray();

        if (forbiddenPropertyNames.Length > 0 || insertNullType && schema.RootElement.TryGetProperty(TypeKey, out var typeElement) &&
            (typeElement.ValueKind == JsonValueKind.Array && !typeElement.EnumerateArray().Any(static t => NullType.Equals(t.GetString(), StringComparison.OrdinalIgnoreCase)) ||
            typeElement.ValueKind == JsonValueKind.String && typeElement.GetString() != NullType))
        {
            var originalSchema = JsonSerializer.Serialize(schema.RootElement);
            var parsedJson = JsonNode.Parse(originalSchema);

            if (parsedJson is null)
            {
                return schema;
            }

            var jsonObject = parsedJson.AsObject();
            foreach (var forbiddenPropertyName in forbiddenPropertyNames)
            {
                jsonObject.Remove(forbiddenPropertyName);
            }

            InsertNullTypeIfRequired(insertNullType, jsonObject);

            return KernelJsonSchema.Parse(jsonObject.ToString());
        }
        return schema;
    }
    // https://platform.openai.com/docs/guides/structured-outputs#some-type-specific-keywords-are-not-yet-supported
    private static void InsertNullTypeIfRequired(bool insertNullType, JsonObject jsonObject)
    {
        if (insertNullType && jsonObject.TryGetPropertyValue(TypeKey, out var typeValue))
        {
            if (typeValue is JsonArray jsonArray && !jsonArray.Contains(NullType))
            {
                jsonArray.Add(NullType);
            }
            else if (typeValue is JsonValue jsonValue && jsonValue.GetValueKind() == JsonValueKind.String)
            {
                jsonObject[TypeKey] = new JsonArray { typeValue.GetValue<string>(), NullType };
            }
        }
    }
    private const string NullType = "null";
    private const string TypeKey = "type";
    // https://platform.openai.com/docs/guides/structured-outputs#some-type-specific-keywords-are-not-yet-supported
    private static readonly string[] s_forbiddenKeywords = [
        "contains",
        "format",
        "maxContains",
        "maximum",
        "maxItems",
        "maxLength",
        "maxProperties",
        "minContains",
        "minimum",
        "minItems",
        "minLength",
        "minProperties",
        "multipleOf",
        "pattern",
        "patternProperties",
        "propertyNames",
        "unevaluatedItems",
        "unevaluatedProperties",
        "uniqueItems",
    ];
}

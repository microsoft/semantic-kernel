// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using Azure.AI.OpenAI;
using Json.Schema;
using Json.Schema.Generation;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

// NOTE: Since this space is evolving rapidly, in order to reduce the risk of needing to take breaking
// changes as OpenAI's APIs evolve, these types are not externally constructible. In the future, once
// things stabilize, and if need demonstrates, we could choose to expose those constructors.

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
    private static readonly BinaryData s_zeroFunctionParametersSchema = new("{\"type\":\"object\",\"required\":[],\"properties\":{}}");

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
    public static string NameSeparator => "_";

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
    /// Converts the <see cref="OpenAIFunction"/> representation to the Azure SDK's
    /// <see cref="FunctionDefinition"/> representation.
    /// </summary>
    /// <returns>A <see cref="FunctionDefinition"/> containing all the function information.</returns>
    public FunctionDefinition ToFunctionDefinition()
    {
        BinaryData resultParameters = s_zeroFunctionParametersSchema;

        IReadOnlyList<OpenAIFunctionParameter>? parameters = this.Parameters;
        if (parameters is { Count: > 0 })
        {
            var properties = new Dictionary<string, KernelJsonSchema>();
            var required = new List<string>();

            for (int i = 0; i < parameters.Count; i++)
            {
                var parameter = parameters[i];

                KernelJsonSchema? schema = parameter.Schema ?? GetJsonSchema(parameter.ParameterType, parameter.Description);
                if (schema is not null)
                {
                    properties.Add(parameter.Name, schema);

                    if (parameter.IsRequired)
                    {
                        required.Add(parameter.Name);
                    }
                }
            }

            resultParameters = BinaryData.FromObjectAsJson(new
            {
                type = "object",
                required,
                properties,
            });
        }

        return new FunctionDefinition
        {
            Name = this.FullyQualifiedName,
            Description = this.Description,
            Parameters = resultParameters,
        };
    }

    /// <summary>
    /// Creates an <see cref="KernelJsonSchema"/> that contains a JSON Schema of the specified <see cref="Type"/> with the specified description.
    /// </summary>
    /// <param name="type">The object Type.</param>
    /// <param name="description">The object description.</param>
    /// <returns>Return JSON Schema document or null if the type is null</returns>
    [return: NotNullIfNotNull("type")]
    internal static KernelJsonSchema? GetJsonSchema(Type? type, string? description)
    {
        KernelJsonSchema? schema = null;
        if (type is not null &&
            !(type.IsPointer || // from RuntimeType.ThrowIfTypeNeverValidGenericArgument
#if NET_8_OR_GREATER
              type.IsFunctionPointer ||
#endif
              type.IsByRef || type == typeof(void)))
        {
            try
            {
                schema = KernelJsonSchema.Parse(JsonSerializer.Serialize(
                    new JsonSchemaBuilder()
                    .FromType(type)
                    .Description(description ?? string.Empty)
                    .Build()));
            }
            catch (ArgumentException)
            {
                // Invalid type; ignore, and leave schema as null
            }
        }

        return schema;
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using Azure.AI.OpenAI;
using Json.Schema;
using Json.Schema.Generation;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Represents a function parameter that can be passed to the OpenAI API
/// </summary>
public class OpenAIFunctionParameter
{
    /// <summary>
    /// Name of the parameter.
    /// </summary>
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Description of the parameter.
    /// </summary>
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// Whether the parameter is required or not.
    /// </summary>
    public bool IsRequired { get; set; } = false;

    /// <summary>
    /// The JSON Schema of the parameter.
    /// </summary>
    public KernelParameterJsonSchema? Schema { get; set; } = null;

    /// <summary>
    /// The <see cref="Type"/> of the parameter.
    /// </summary>
    public Type? ParameterType { get; set; } = null;
}

/// <summary>
/// Represents a return parameter of a function that can be passed to the OpenAI API
/// </summary>
public class OpenAIFunctionReturnParameter
{
    /// <summary>
    /// Description of the parameter.
    /// </summary>
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// The JSON Schema of the parameter.
    /// </summary>
    public KernelParameterJsonSchema? Schema { get; set; } = null;

    /// <summary>
    /// The <see cref="Type"/> of the return parameter.
    /// </summary>
    public Type? ParameterType { get; set; } = null;
}

/// <summary>
/// Represents a function that can be passed to the OpenAI API
/// </summary>
public class OpenAIFunction
{
    /// <summary>
    /// Cached <see cref="BinaryData"/> storing the JSON for a function with no parameters.
    /// </summary>
    /// <remarks>
    /// This is an optimization to avoid serializing the same JSON Schema over and over again
    /// for this relatively common case.
    /// </remarks>
    private static readonly BinaryData s_zeroFunctionParametersSchema = new("{\"type\":\"object\",\"required\":[],\"properties\":{}}");

    /// <summary>
    /// Separator between the plugin name and the function name
    /// </summary>
    public const string NameSeparator = "_";

    /// <summary>
    /// Name of the function
    /// </summary>
    public string FunctionName { get; set; } = string.Empty;

    /// <summary>
    /// Name of the function's associated plugin, if applicable
    /// </summary>
    public string PluginName { get; set; } = string.Empty;

    /// <summary>
    /// Fully qualified name of the function. This is the concatenation of the plugin name and the function name,
    /// separated by the value of <see cref="NameSeparator"/>.
    /// If there is no plugin name, this is the same as the function name.
    /// </summary>
    public string FullyQualifiedName =>
        string.IsNullOrEmpty(this.PluginName) ? this.FunctionName : $"{this.PluginName}{NameSeparator}{this.FunctionName}";

    /// <summary>
    /// Description of the function
    /// </summary>
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// List of parameters for the function
    /// </summary>
    public IList<OpenAIFunctionParameter> Parameters { get; set; } = new List<OpenAIFunctionParameter>();

    /// <summary>
    /// The return parameter of the function.
    /// </summary>
    public OpenAIFunctionReturnParameter ReturnParameter { get; set; } = new OpenAIFunctionReturnParameter();

    /// <summary>
    /// Converts the <see cref="OpenAIFunction"/> to OpenAI's <see cref="FunctionDefinition"/>.
    /// </summary>
    /// <returns>A <see cref="FunctionDefinition"/> containing all the function information.</returns>
    public FunctionDefinition ToFunctionDefinition()
    {
        BinaryData resultParameters = s_zeroFunctionParametersSchema;

        var parameters = this.Parameters;
        if (parameters.Count > 0)
        {
            var properties = new Dictionary<string, KernelParameterJsonSchema>();
            var required = new List<string>();

            for (int i = 0; i < parameters.Count; i++)
            {
                var parameter = parameters[i];

                KernelParameterJsonSchema? schema = parameter.Schema ?? GetJsonSchema(parameter.ParameterType, parameter.Description);
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
                required = required,
                properties = properties,
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
    /// Creates an <see cref="KernelParameterJsonSchema"/> that contains a JSON Schema of the specified <see cref="Type"/> with the specified description.
    /// </summary>
    /// <param name="type">The object Type.</param>
    /// <param name="description">The object description.</param>
    /// <returns>Return JSON Schema document or null if the type is null</returns>
    [return: NotNullIfNotNull("type")]
    internal static KernelParameterJsonSchema? GetJsonSchema(Type? type, string? description)
    {
        KernelParameterJsonSchema? schema = null;
        if (type is not null)
        {
            schema = KernelParameterJsonSchema.Parse(JsonSerializer.Serialize(
                new JsonSchemaBuilder()
                .FromType(type)
                .Description(description ?? string.Empty)
                .Build()));
        }

        return schema;
    }
}

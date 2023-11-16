// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using Azure.AI.OpenAI;
using Json.More;
using Json.Schema;
using Json.Schema.Generation;
using Microsoft.SemanticKernel.Extensions;
using Microsoft.SemanticKernel.Text;

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
    /// Type of the parameter.
    /// </summary>
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// Whether the parameter is required or not.
    /// </summary>
    public bool IsRequired { get; set; } = false;

    /// <summary>
    /// The Json Schema of the parameter.
    /// </summary>
    public JsonDocument? Schema { get; set; } = null;

    /// <summary>
    /// The parameter Type.
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
    /// The Json Schema of the parameter.
    /// </summary>
    public JsonDocument? Schema { get; set; } = null;

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
        this.PluginName.IsNullOrEmpty() ? this.FunctionName : $"{this.PluginName}{NameSeparator}{this.FunctionName}";

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
        JsonDocument schemaBuilderDelegate(Type type, string description)
        {
            var schema = new JsonSchemaBuilder()
                .FromType(type)
                .Description(description ?? string.Empty)
                .Build()
                .ToJsonDocument();

            return schema;
        }

        JsonSchemaFunctionManual jsonSchemaManual = this.ToFunctionView().ToJsonSchemaManual(schemaBuilderDelegate, false);

        return new FunctionDefinition
        {
            Name = this.FullyQualifiedName,
            Description = this.Description,
            Parameters = BinaryData.FromObjectAsJson(jsonSchemaManual.Parameters),
        };
    }
}

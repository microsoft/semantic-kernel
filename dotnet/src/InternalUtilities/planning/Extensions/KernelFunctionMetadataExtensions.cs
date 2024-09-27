// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Provides extension methods for the <see cref="KernelFunctionMetadata"/> class.
/// </summary>
internal static class KernelFunctionMetadataExtensions
{
    private const string SuccessfulResponseCode = "200";
    private const string SuccessfulResponseDescription = "Success";

    /// <summary>
    /// Creates a <see cref="JsonSchemaFunctionView"/> for a function.
    /// </summary>
    /// <param name="function">The function.</param>
    /// <param name="includeOutputSchema">Indicates if the schema should include information about the output or return type of the function.</param>
    /// <param name="nameDelimiter">The delimiter to use between the plugin name and the function name.</param>
    /// <returns>An instance of <see cref="JsonSchemaFunctionView"/></returns>
    public static JsonSchemaFunctionView ToJsonSchemaFunctionView(this KernelFunctionMetadata function, bool includeOutputSchema = true, string nameDelimiter = "-")
    {
        var functionView = new JsonSchemaFunctionView
        {
            Name = $"{function.PluginName}{nameDelimiter}{function.Name}",
            Description = function.Description,
        };

        var requiredProperties = new List<string>();
        foreach (var parameter in function.Parameters)
        {
            var schema = parameter.Schema;
            if (schema is not null)
            {
                functionView.Parameters.Properties.Add(parameter.Name, schema);
            }
            if (parameter.IsRequired)
            {
                requiredProperties.Add(parameter.Name);
            }
        }

        if (includeOutputSchema)
        {
            var functionResponse = new JsonSchemaFunctionResponse
            {
                Description = SuccessfulResponseDescription
            };

            functionResponse.Content.JsonResponse.Schema = function.ReturnParameter.Schema;

            functionView.FunctionResponses.Add(SuccessfulResponseCode, functionResponse);
        }

        functionView.Parameters.Required = requiredProperties;
        return functionView;
    }

    /// <summary>
    /// Create a manual-friendly string for a function.
    /// </summary>
    /// <param name="function">The function to create a manual-friendly string for.</param>
    /// <returns>A manual-friendly string for a function.</returns>
    internal static string ToManualString(this KernelFunctionMetadata function)
    {
        var inputs = string.Join("\n", function.Parameters.Select(parameter =>
        {
            var defaultValueString = InternalTypeConverter.ConvertToString(parameter.DefaultValue);
            defaultValueString = string.IsNullOrEmpty(defaultValueString) ? string.Empty : $" (default value: {defaultValueString})";
            return $"    - {parameter.Name}: {parameter.Description}{defaultValueString}";
        }));

        // description and inputs are indented by 2 spaces
        // While each parameter in inputs is indented by 4 spaces
        return $"{function.ToFullyQualifiedName()}:  description: {function.Description}  inputs:{inputs}";
    }

    /// <summary>
    /// Create a fully qualified name for a function.
    /// </summary>
    /// <param name="function">The function to create a fully qualified name for.</param>
    /// <returns>A fully qualified name for a function.</returns>
    internal static string ToFullyQualifiedName(this KernelFunctionMetadata function)
    {
        return $"{function.PluginName}.{function.Name}";
    }

    /// <summary>
    /// Create a string for generating an embedding for a function.
    /// </summary>
    /// <param name="function">The function to create a string for generating an embedding for.</param>
    /// <returns>A string for generating an embedding for a function.</returns>
    internal static string ToEmbeddingString(this KernelFunctionMetadata function)
    {
        var inputs = string.Join("\n", function.Parameters.Select(p => $"    - {p.Name}: {p.Description}"));
        return $"{function.Name}:\n  description: {function.Description}\n  inputs:\n{inputs}";
    }
}

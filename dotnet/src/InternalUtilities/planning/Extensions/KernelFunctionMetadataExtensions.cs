// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;

#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel.Planning;
#pragma warning restore IDE0130

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
    /// <param name="jsonSchemaDelegate">A delegate that creates a JSON Schema from a <see cref="Type"/> and a semantic description.</param>
    /// <param name="includeOutputSchema">Indicates if the schema should include information about the output or return type of the function.</param>
    /// <returns>An instance of <see cref="JsonSchemaFunctionView"/></returns>
    public static JsonSchemaFunctionView ToJsonSchemaFunctionView(this KernelFunctionMetadata function, Func<Type?, string?, KernelJsonSchema?> jsonSchemaDelegate, bool includeOutputSchema = true)
    {
        var functionView = new JsonSchemaFunctionView
        {
            Name = $"{function.PluginName}_{function.Name}",
            Description = function.Description,
        };

        var requiredProperties = new List<string>();
        foreach (var parameter in function.Parameters)
        {
            var schema = parameter.Schema ?? jsonSchemaDelegate(parameter.ParameterType, parameter.Description);
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

            var schema = function.ReturnParameter.Schema ?? jsonSchemaDelegate(function.ReturnParameter.ParameterType, SuccessfulResponseDescription);
            functionResponse.Content.JsonResponse.Schema = schema;

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
            var defaultValueString = string.IsNullOrEmpty(parameter.DefaultValue) ? string.Empty : $" (default value: {parameter.DefaultValue})";
            return $"    - {parameter.Name}: {parameter.Description}{defaultValueString}";
        }));

        // description and inputs are indented by 2 spaces
        // While each parameter in inputs is indented by 4 spaces
        return $@"{function.ToFullyQualifiedName()}:
  description: {function.Description}
  inputs:
{inputs}";
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

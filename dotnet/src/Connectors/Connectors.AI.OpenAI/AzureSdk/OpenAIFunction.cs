// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Azure.AI.OpenAI;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Represents a function parameter that can be pass to the OpenAI API
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
    public string Type { get; set; } = string.Empty; // TODO: enum?

    /// <summary>
    /// Whether the parameter is required or not.
    /// </summary>
    public bool IsRequired { get; set; } = false;
}

/// <summary>
/// Represents a function that can be pass to the OpenAI API
/// </summary>
public class OpenAIFunction
{
    /// <summary>
    /// Name of the function
    /// </summary>
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Description of the function
    /// </summary>
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// List of parameters for the function
    /// </summary>
    public IList<OpenAIFunctionParameter> Parameters { get; set; } = new List<OpenAIFunctionParameter>();

    /// <summary>
    /// Converts the <see cref="OpenAIFunction"/> to OpenAI's <see cref="FunctionDefinition"/>.
    /// </summary>
    /// <returns>A <see cref="FunctionDefinition"/> containing all the function information.</returns>
    public FunctionDefinition ToFunctionDefinition()
    {
        var requiredParams = new List<string>();

        var paramProperties = new Dictionary<string, object>();
        foreach (var param in this.Parameters)
        {
            paramProperties.Add(
                param.Name,
                new
                {
                    type = param.Type,
                    description = param.Description,
                });

            if (param.IsRequired)
            {
                requiredParams.Add(param.Name);
            }
        }

        return new FunctionDefinition
        {
            Name = this.Name,
            Description = this.Description,
            Parameters = BinaryData.FromObjectAsJson(
                new
                {
                    type = "object",
                    properties = paramProperties,
                    required = requiredParams,
                }),
        };
    }
}

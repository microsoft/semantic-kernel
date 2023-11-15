// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Extensions;

internal static class ISKFunctionExtensions
{
    /// <summary>
    /// Produce a fully qualified toolname.
    /// </summary>
    public static string GetQualifiedName(this ISKFunction function)
    {
        return
            string.IsNullOrWhiteSpace(function.PluginName) ?
            function.Name :
            $"{function.PluginName}-{function.Name}";
    }

    /// <summary>
    /// Convert <see cref="ISKFunction"/> to an OpenAI tool model.
    /// </summary>
    /// <param name="function">The source function</param>
    /// <returns>An OpenAI tool model</returns>
    public static ToolModel ToToolModel(this ISKFunction function)
    {
        var view = function.Describe();
        var required = new List<string>(view.Parameters.Count);
        var properties =
            view.Parameters.ToDictionary(
                p => p.Name,
                p =>
                {
                    if (p.IsRequired ?? false)
                    {
                        required.Add(p.Name);
                    }

                    return
                        new OpenAIParameter
                        {
                            Type = p.Type?.Name ?? "string", // $$$
                            Description = p.Description,
                        };
                });

        var payload =
            new ToolModel
            {
                Type = "function",
                Function =
                    new()
                    {
                        Name = function.GetQualifiedName(),
                        Description = function.Description,
                        Parameters =
                                new OpenAIParameters
                                {
                                    Properties = properties,
                                    Required = required,
                                },
                    },
            };

        return payload;
    }
}

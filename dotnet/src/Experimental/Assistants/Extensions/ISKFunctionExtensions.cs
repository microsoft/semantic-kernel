// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Experimental.Assistants.Models;
using System.Collections.Generic;
using System.Linq;

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
    public static AssistantModel.ToolModel ToToolModel(this ISKFunction function)
    {
        var view = function.Describe();
        var required = new List<string>(view.Parameters.Count);
        var parameters =
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
                            Type = p.Type?.Name ?? nameof(System.String),
                            Description = p.Description,
                        };
                });

        var payload =
            new AssistantModel.ToolModel
            {
                Type = "function",
                Function =
                    new()
                    {
                        Name = function.GetQualifiedName(),
                        Description = function.Description,
                        Parameters =
                        {
                            Properties = parameters,
                            Required = required,
                        }
                    },
            };

        return payload;
    }
}

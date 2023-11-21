// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using Json.More;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Extensions;

internal static class ISKFunctionExtensions
{
    /// <summary>
    /// Produce a fully qualified toolname.
    /// </summary>
    public static string GetQualifiedName(this ISKFunction function, string pluginName)
    {
        return $"{pluginName}-{function.Name}";
    }

    /// <summary>
    /// Convert <see cref="ISKFunction"/> to an OpenAI tool model.
    /// </summary>
    /// <param name="function">The source function</param>
    /// <param name="pluginName">The plugin name</param>
    /// <returns>An OpenAI tool model</returns>
    public static ToolModel ToToolModel(this ISKFunction function, string pluginName)
    {
        var view = function.GetMetadata();
        var required = new List<string>(view.Parameters.Count);
        var properties =
            view.Parameters.ToDictionary(
                p => p.Name,
                p =>
                {
                    if (p.IsRequired)
                    {
                        required.Add(p.Name);
                    }

                    return
                        new OpenAIParameter
                        {
                            Type = ConvertType(p.ParameterType),
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
                        Name = function.GetQualifiedName(pluginName),
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

    /// <summary>
    /// Invoke the <see cref="ISKFunction"/> in streaming mode.
    /// </summary>
    /// <param name="function">Target function</param>
    /// <param name="kernel">The kernel</param>
    /// <param name="context">SK context</param>
    /// <param name="requestSettings">LLM completion settings (for semantic functions only)</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A asynchronous list of streaming result chunks</returns>
    public static IAsyncEnumerable<StreamingResultChunk> InvokeStreamingAsync(
        this ISKFunction function,
        Kernel kernel,
        SKContext context,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        return function.InvokeStreamingAsync<StreamingResultChunk>(kernel, context, requestSettings, cancellationToken);
    }

    private static string ConvertType(Type? type)
    {
        if (type == null || type == typeof(string))
        {
            return "string";
        }

        if (type.IsNumber())
        {
            return "number";
        }

        if (type.IsEnum)
        {
            return "enum";
        }

        return type.Name;
    }
}

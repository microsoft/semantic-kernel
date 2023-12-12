// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Represents a query string builder for REST API operations.
/// </summary>
internal static class QueryStringBuilder
{
    /// <summary>
    /// Query string parameter serializers.
    /// </summary>
    private static readonly Dictionary<RestApiOperationParameterStyle, Func<RestApiOperationParameter, string, string>> s_queryStringParameterSerializers = new()
    {
        { RestApiOperationParameterStyle.Form, FormStyleParameterSerializer.Serialize },
        { RestApiOperationParameterStyle.SpaceDelimited, SpaceDelimitedStyleParameterSerializer.Serialize },
        { RestApiOperationParameterStyle.PipeDelimited, PipeDelimitedStyleParameterSerializer.Serialize }
    };

    ///<inheritdoc/>
    public static string BuildQueryString(this RestApiOperation operation, IDictionary<string, string> arguments)
    {
        var segments = new List<string>();

        var parameters = operation.Parameters.Where(p => p.Location == RestApiOperationParameterLocation.Query);

        foreach (var parameter in parameters)
        {
            if (!arguments.TryGetValue(parameter.Name, out string? argument) || argument is null)
            {
                //Throw an exception if the parameter is a required one but no value is provided.
                if (parameter.IsRequired)
                {
                    throw new KernelException($"No argument or value is provided for the '{parameter.Name}' required parameter of the operation - '{operation.Id}'.");
                }

                //Skipping not required parameter if no argument provided for it.
                continue;
            }

            var parameterStyle = parameter.Style ?? RestApiOperationParameterStyle.Form;

            if (!s_queryStringParameterSerializers.TryGetValue(parameterStyle, out var serializer))
            {
                throw new KernelException($"The query string parameter '{parameterStyle}' serialization style is not supported.");
            }

            //Serializing the parameter and adding it to the query string if there's an argument for it.
            segments.Add(serializer.Invoke(parameter, argument));
        }

        return string.Join("&", segments);
    }
}

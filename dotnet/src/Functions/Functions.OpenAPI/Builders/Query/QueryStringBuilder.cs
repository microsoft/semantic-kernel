// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Functions.OpenAPI.Builders.Serialization;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Builders.Query;

/// <summary>
/// Represents a query string builder for REST API operations.
/// </summary>
internal sealed class QueryStringBuilder : IQueryStringBuilder
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
    public string Build(RestApiOperation operation, IDictionary<string, string> arguments)
    {
        var segments = new List<string>();

        var parameters = operation.Parameters.Where(p => p.Location == RestApiOperationParameterLocation.Query);

        foreach (var parameter in parameters)
        {
            if (!arguments.TryGetValue(parameter.Name, out var argument))
            {
                //Throw an exception if the parameter is a required one but no value is provided.
                if (parameter.IsRequired)
                {
                    throw new SKException($"No argument found for the `{parameter.Name}` required parameter");
                }

                //Skipping not required parameter if no argument provided for it.
                continue;
            }

            var parameterStyle = parameter.Style ?? RestApiOperationParameterStyle.Form;

            if (!s_queryStringParameterSerializers.TryGetValue(parameterStyle, out var serializer))
            {
                throw new SKException($"The query string parameter `{parameterStyle}` serialization style is not supported.");
            }

            //Serializing the parameter and adding it to the query string if there's an argument for it.
            segments.Add(serializer.Invoke(parameter, argument));
        }

        return string.Join("&", segments);
    }
}

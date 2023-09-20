// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Web;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Builders.Query;

/// <summary>
/// Represents a query string builder for REST API operations.
/// </summary>
internal class QueryStringBuilder : IQueryStringBuilder
{
    ///<inheritdoc/>
    public string Build(RestApiOperation operation, IDictionary<string, string> arguments)
    {
        var queryStringSegments = new List<string>();

        var queryStringParameters = operation.Parameters.Where(p => p.Location == RestApiOperationParameterLocation.Query);

        foreach (var parameter in queryStringParameters)
        {
            //Resolve argument for the parameter.
            if (!arguments.TryGetValue(parameter.Name, out var argument))
            {
                argument = parameter.DefaultValue;
            }

            //Add the parameter to the query string if there's an argument for it.
            if (!string.IsNullOrEmpty(argument))
            {
                queryStringSegments.Add($"{parameter.Name}={HttpUtility.UrlEncode(argument)}");
                continue;
            }

            //Throw an exception if the parameter is a required one but no value is provided.
            if (parameter.IsRequired)
            {
                throw new SKException($"No argument found for required query string parameter - '{parameter.Name}' for operation - '{operation.Id}'");
            }
        }

        return string.Join("&", queryStringSegments);
    }
}

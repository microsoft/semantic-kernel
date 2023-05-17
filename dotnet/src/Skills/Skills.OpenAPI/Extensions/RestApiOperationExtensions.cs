// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text.RegularExpressions;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Skills.OpenAPI.Model;
#pragma warning restore IDE0130

/// <summary>
/// Class for extensions methods for the <see cref="RestApiOperation"/> class.
/// </summary>
internal static class RestApiOperationExtensions
{
    /// <summary>
    /// Returns list of REST API operation parameters.
    /// </summary>
    /// <param name="operation">The REST API operation.</param>
    /// <param name="serverUrlOverride">The server URL override.</param>
    /// <returns>The list of parameters.</returns>
    public static IReadOnlyList<RestApiOperationParameter> GetParameters(this RestApiOperation operation, Uri? serverUrlOverride = null)
    {
        var parameters = new List<RestApiOperationParameter>(operation.Parameters)
        {
            // Register the "server-url" parameter if override is provided
            new RestApiOperationParameter(
                RestApiOperation.ServerUrlArgumentName,
                "string",
                false,
                RestApiOperationParameterLocation.Path,
                RestApiOperationParameterStyle.Simple,
                defaultValue: serverUrlOverride?.AbsoluteUri ?? operation.ServerUrl?.AbsoluteUri)
        };

        // Register the "payload" parameter to be advertised for Put and Post operations.
        if (operation.Method == HttpMethod.Put || operation.Method == HttpMethod.Post)
        {
            var type = operation.Payload?.MediaType == MediaTypeTextPlain ? "string" : "object";

            parameters.Add(new RestApiOperationParameter(
                RestApiOperation.PayloadArgumentName,
                type,
                true,
                RestApiOperationParameterLocation.Body,
                RestApiOperationParameterStyle.Simple,
                description: operation.Payload?.Description ?? "REST API request body."));

            parameters.Add(new RestApiOperationParameter(
                RestApiOperation.ContentTypeArgumentName,
                "string",
                false,
                RestApiOperationParameterLocation.Body,
                RestApiOperationParameterStyle.Simple,
                description: "Content type of REST API request body."));
        }

        // Create a property alternative name without special symbols that are not supported by SK template language.
        foreach (var parameter in parameters)
        {
            parameter.AlternativeName = s_invalidSymbolsRegex.Replace(parameter.Name, "_");
        }

        return parameters;
    }

    private const string MediaTypeTextPlain = "text/plain";
    private static readonly Regex s_invalidSymbolsRegex = new("[^0-9A-Za-z_]+");
}

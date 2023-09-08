// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.RegularExpressions;
using System.Web;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Model;

/// <summary>
/// The REST API operation.
/// </summary>
public sealed class RestApiOperation
{
    /// <summary>
    /// An artificial parameter that is added to be able to override REST API operation server url.
    /// </summary>
    public const string ServerUrlArgumentName = "server-url";

    /// <summary>
    /// An artificial parameter to be used for operation having "text/plain" payload media type.
    /// </summary>
    public const string PayloadArgumentName = "payload";

    /// <summary>
    /// An artificial parameter to be used for indicate payload media-type if it's missing in payload metadata.
    /// </summary>
    public const string ContentTypeArgumentName = "content-type";

    /// <summary>
    /// The operation identifier.
    /// </summary>
    public string Id { get; }

    /// <summary>
    /// The operation description.
    /// </summary>
    public string Description { get; }

    /// <summary>
    /// The operation path.
    /// </summary>
    public string Path { get; }

    /// <summary>
    /// The operation method - GET, POST, PUT, DELETE.
    /// </summary>
    public HttpMethod Method { get; }

    /// <summary>
    /// The server URL.
    /// </summary>
    public Uri? ServerUrl { get; }

    /// <summary>
    /// The operation headers.
    /// </summary>
    public IDictionary<string, string> Headers { get; }

    /// <summary>
    /// The operation parameters.
    /// </summary>
    public IList<RestApiOperationParameter> Parameters { get; }

    /// <summary>
    /// The operation payload.
    /// </summary>
    public RestApiOperationPayload? Payload { get; }

    /// <summary>
    /// Creates an instance of a <see cref="RestApiOperation"/> class.
    /// </summary>
    /// <param name="id">The operation identifier.</param>
    /// <param name="serverUrl">The server URL.</param>
    /// <param name="path">The operation path.</param>
    /// <param name="method">The operation method.</param>
    /// <param name="description">The operation description.</param>
    /// <param name="parameters">The operation parameters.</param>
    /// <param name="headers">The operation headers.</param>
    /// <param name="payload">The operation payload.</param>
    public RestApiOperation(
        string id,
        Uri? serverUrl,
        string path,
        HttpMethod method,
        string description,
        IList<RestApiOperationParameter> parameters,
        IDictionary<string, string> headers,
        RestApiOperationPayload? payload = null)
    {
        this.Id = id;
        this.ServerUrl = serverUrl;
        this.Path = path;
        this.Method = method;
        this.Description = description;
        this.Parameters = parameters;
        this.Headers = headers;
        this.Payload = payload;
    }

    /// <summary>
    /// Builds operation Url.
    /// </summary>
    /// <param name="arguments">The operation arguments.</param>
    /// <param name="serverUrlOverride">Override for REST API operation server url.</param>
    /// <param name="apiHostUrl">The URL of REST API host.</param>
    /// <returns>The operation Url.</returns>
    public Uri BuildOperationUrl(IDictionary<string, string> arguments, Uri? serverUrlOverride = null, Uri? apiHostUrl = null)
    {
        var path = this.ReplacePathParameters(this.Path, arguments);

        path = this.AddQueryString(path, arguments);

        string serverUrlString;

        if (serverUrlOverride is not null)
        {
            serverUrlString = serverUrlOverride.AbsoluteUri;
        }
        else if (arguments.TryGetValue(ServerUrlArgumentName, out string serverUrlFromArgument))
        {
            // Override defined server url - https://api.example.com/v1 by the one from arguments.
            serverUrlString = serverUrlFromArgument;
        }
        else
        {
            serverUrlString =
                this.ServerUrl?.AbsoluteUri ??
                apiHostUrl?.AbsoluteUri ??
                throw new InvalidOperationException($"Server url is not defined for operation {this.Id}");
        }

        // make sure base url ends with trailing slash
        if (!serverUrlString.EndsWith("/", StringComparison.OrdinalIgnoreCase))
        {
            serverUrlString += "/";
        }

        return new Uri(new Uri(serverUrlString), $"{path.TrimStart('/')}");
    }

    /// <summary>
    /// Renders operation request headers.
    /// </summary>
    /// <param name="arguments">The operation arguments.</param>
    /// <returns>The rendered request headers.</returns>
    public IDictionary<string, string> RenderHeaders(IDictionary<string, string> arguments)
    {
        var headers = new Dictionary<string, string>();

        foreach (var header in this.Headers)
        {
            var headerName = header.Key;
            var headerValue = header.Value;

            //A try to resolve header value in arguments.
            if (arguments.TryGetValue(headerName, out var value))
            {
                headers.Add(headerName, value);
                continue;
            }

            //Header value is already supplied.
            if (!string.IsNullOrEmpty(headerValue))
            {
                headers.Add(headerName, headerValue);
                continue;
            }

            //Getting metadata for the header
            var headerMetadata = this.Parameters.FirstOrDefault(p => p.Location == RestApiOperationParameterLocation.Header && p.Name == headerName)
                                 ?? throw new SKException($"No value for the '{headerName} header is found.'");

            //If parameter is required it's value should always be provided.
            if (headerMetadata.IsRequired)
            {
                throw new SKException($"No value for the '{headerName} header is found.'");
            }

            //Parameter is not required and no default value provided.
            if (string.IsNullOrEmpty(headerMetadata.DefaultValue))
            {
                continue;
            }

            //Using default value.
            headers.Add(headerName, headerMetadata.DefaultValue!);
        }

        return headers;
    }

    #region private

    /// <summary>
    /// Replaces path parameters by corresponding arguments.
    /// </summary>
    /// <param name="path">Operation path to replace parameters in.</param>
    /// <param name="arguments">Arguments to replace parameters by.</param>
    /// <returns>Path with replaced parameters</returns>
    private string ReplacePathParameters(string path, IDictionary<string, string> arguments)
    {
        string ReplaceParameter(Match match)
        {
            var parameterName = match.Groups[1].Value;

            //A try to find parameter value in arguments
            if (arguments.TryGetValue(parameterName, out var value))
            {
                return value;
            }

            //A try to find default value for the parameter
            var parameterMetadata = this.Parameters.First(p => p.Location == RestApiOperationParameterLocation.Path && p.Name == parameterName);
            if (parameterMetadata?.DefaultValue == null)
            {
                throw new SKException($"No argument found for parameter - '{parameterName}' for operation - '{this.Id}'");
            }

            return parameterMetadata.DefaultValue;
        }

        return s_urlParameterMatch.Replace(path, ReplaceParameter);
    }

    /// <summary>
    /// Adds query string to the operation path.
    /// </summary>
    /// <param name="path">The operation path.</param>
    /// <param name="arguments">The operation arguments.</param>
    /// <returns>Path with query string.</returns>
    private string AddQueryString(string path, IDictionary<string, string> arguments)
    {
        var queryStringSegments = new List<string>();

        var queryStringParameters = this.Parameters.Where(p => p.Location == RestApiOperationParameterLocation.Query);

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
                throw new SKException($"No argument found for required query string parameter - '{parameter.Name}' for operation - '{this.Id}'");
            }
        }

        var queryString = string.Join("&", queryStringSegments);

        return string.IsNullOrEmpty(queryString) ? path : $"{path}?{queryString}";
    }

    private static readonly Regex s_urlParameterMatch = new(@"\{([\w-]+)\}");

    # endregion
}

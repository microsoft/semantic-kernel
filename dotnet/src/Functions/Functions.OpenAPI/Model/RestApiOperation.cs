// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.RegularExpressions;

namespace Microsoft.SemanticKernel.Plugins.OpenApi.Model;

/// <summary>
/// The REST API operation.
/// </summary>
public sealed class RestApiOperation
{
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
    /// The list of possible operation responses.
    /// </summary>
    public IDictionary<string, RestApiOperationExpectedResponse> Responses { get; }

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
    /// <param name="responses">The operation responses.</param>
    public RestApiOperation(
        string id,
        Uri? serverUrl,
        string path,
        HttpMethod method,
        string description,
        IList<RestApiOperationParameter> parameters,
        IDictionary<string, string> headers,
        RestApiOperationPayload? payload = null,
        IDictionary<string, RestApiOperationExpectedResponse>? responses = null)
    {
        this.Id = id;
        this.ServerUrl = serverUrl;
        this.Path = path;
        this.Method = method;
        this.Description = description;
        this.Parameters = parameters;
        this.Headers = headers;
        this.Payload = payload;
        this.Responses = responses ?? new Dictionary<string, RestApiOperationExpectedResponse>();
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
        var serverUrl = this.GetServerUrl(serverUrlOverride, apiHostUrl);

        var path = this.ReplacePathParameters(this.Path, arguments);

        return new Uri(serverUrl, $"{path.TrimStart('/')}");
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
            if (arguments.TryGetValue(headerName, out string? value) && value is not null)
            {
                headers.Add(headerName, value!);
                continue;
            }

            //Header value is already supplied.
            if (!string.IsNullOrEmpty(headerValue))
            {
                headers.Add(headerName, headerValue!);
                continue;
            }

            //Getting metadata for the header
            var headerMetadata = this.Parameters.FirstOrDefault(p => p.Location == RestApiOperationParameterLocation.Header && p.Name == headerName)
                                 ?? throw new KernelException($"No argument or value is provided for the '{headerName}' header of the operation - '{this.Id}'.");

            //If parameter is required it's value should always be provided.
            if (headerMetadata.IsRequired)
            {
                throw new KernelException($"No argument or value is provided for the '{headerName}' required header of the operation - '{this.Id}'.'");
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
            if (arguments.TryGetValue(parameterName, out string? value) && value is not null)
            {
                return value;
            }

            //A try to find default value for the parameter
            var parameterMetadata = this.Parameters.First(p => p.Location == RestApiOperationParameterLocation.Path && p.Name == parameterName);
            if (parameterMetadata?.DefaultValue == null)
            {
                throw new KernelException($"No argument or value is provided for the '{parameterName}' parameter of the operation - '{this.Id}'.");
            }

            return parameterMetadata.DefaultValue;
        }

        return s_urlParameterMatch.Replace(path, ReplaceParameter);
    }

    /// <summary>
    /// Returns operation server Url.
    /// </summary>
    /// <param name="serverUrlOverride">Override for REST API operation server url.</param>
    /// <param name="apiHostUrl">The URL of REST API host.</param>
    /// <returns>The operation server url.</returns>
    private Uri GetServerUrl(Uri? serverUrlOverride, Uri? apiHostUrl)
    {
        string serverUrlString;

        if (serverUrlOverride is not null)
        {
            serverUrlString = serverUrlOverride.AbsoluteUri;
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

        return new Uri(serverUrlString);
    }

    private static readonly Regex s_urlParameterMatch = new(@"\{([\w-]+)\}");

    # endregion
}

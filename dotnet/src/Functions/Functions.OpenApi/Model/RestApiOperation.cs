﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.Json.Nodes;
using System.Web;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// The REST API operation.
/// </summary>
public sealed class RestApiOperation
{
    /// <summary>
    /// A static empty dictionary to default to when none is provided.
    /// </summary>
    private static readonly Dictionary<string, object?> s_emptyDictionary = [];

    /// <summary>
    /// Gets the name of an artificial parameter to be used for operation having "text/plain" payload media type.
    /// </summary>
    public static string PayloadArgumentName => "payload";

    /// <summary>
    /// Gets the name of an artificial parameter to be used for indicate payload media-type if it's missing in payload metadata.
    /// </summary>
    public static string ContentTypeArgumentName => "content-type";

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
    /// The server.
    /// </summary>
    public RestApiOperationServer Server { get; }

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
    /// Additional unstructured metadata about the operation.
    /// </summary>
    public IReadOnlyDictionary<string, object?> Extensions { get; init; } = s_emptyDictionary;

    /// <summary>
    /// Creates an instance of a <see cref="RestApiOperation"/> class.
    /// </summary>
    /// <param name="id">The operation identifier.</param>
    /// <param name="server">The server.</param>
    /// <param name="path">The operation path.</param>
    /// <param name="method">The operation method.</param>
    /// <param name="description">The operation description.</param>
    /// <param name="parameters">The operation parameters.</param>
    /// <param name="payload">The operation payload.</param>
    /// <param name="responses">The operation responses.</param>
    public RestApiOperation(
        string id,
        RestApiOperationServer server,
        string path,
        HttpMethod method,
        string description,
        IList<RestApiOperationParameter> parameters,
        RestApiOperationPayload? payload = null,
        IDictionary<string, RestApiOperationExpectedResponse>? responses = null)
    {
        this.Id = id;
        this.Server = server;
        this.Path = path;
        this.Method = method;
        this.Description = description;
        this.Parameters = parameters;
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
    public Uri BuildOperationUrl(IDictionary<string, object?> arguments, Uri? serverUrlOverride = null, Uri? apiHostUrl = null)
    {
        var serverUrl = this.GetServerUrl(serverUrlOverride, apiHostUrl, arguments);

        var path = this.BuildPath(this.Path, arguments);

        return new Uri(serverUrl, $"{path.TrimStart('/')}");
    }

    /// <summary>
    /// Builds operation request headers.
    /// </summary>
    /// <param name="arguments">The operation arguments.</param>
    /// <returns>The request headers.</returns>
    public IDictionary<string, string> BuildHeaders(IDictionary<string, object?> arguments)
    {
        var headers = new Dictionary<string, string>();

        var parameters = this.Parameters.Where(p => p.Location == RestApiOperationParameterLocation.Header);

        foreach (var parameter in parameters)
        {
            if (!arguments.TryGetValue(parameter.Name, out object? argument) || argument is null)
            {
                // Throw an exception if the parameter is a required one but no value is provided.
                if (parameter.IsRequired)
                {
                    throw new KernelException($"No argument is provided for the '{parameter.Name}' required parameter of the operation - '{this.Id}'.");
                }

                // Skipping not required parameter if no argument provided for it.
                continue;
            }

            var parameterStyle = parameter.Style ?? RestApiOperationParameterStyle.Simple;

            if (!s_parameterSerializers.TryGetValue(parameterStyle, out var serializer))
            {
                throw new KernelException($"The headers parameter '{parameterStyle}' serialization style is not supported.");
            }

            var node = OpenApiTypeConverter.Convert(parameter.Name, parameter.Type, argument);

            //Serializing the parameter and adding it to the headers.
            headers.Add(parameter.Name, serializer.Invoke(parameter, node));
        }

        return headers;
    }

    /// <summary>
    /// Builds the operation query string.
    /// </summary>
    /// <param name="arguments">The operation arguments.</param>
    /// <returns>The query string.</returns>
    public string BuildQueryString(IDictionary<string, object?> arguments)
    {
        var segments = new List<string>();

        var parameters = this.Parameters.Where(p => p.Location == RestApiOperationParameterLocation.Query);

        foreach (var parameter in parameters)
        {
            if (!arguments.TryGetValue(parameter.Name, out object? argument) || argument is null)
            {
                // Throw an exception if the parameter is a required one but no value is provided.
                if (parameter.IsRequired)
                {
                    throw new KernelException($"No argument or value is provided for the '{parameter.Name}' required parameter of the operation - '{this.Id}'.");
                }

                // Skipping not required parameter if no argument provided for it.
                continue;
            }

            var parameterStyle = parameter.Style ?? RestApiOperationParameterStyle.Form;

            if (!s_parameterSerializers.TryGetValue(parameterStyle, out var serializer))
            {
                throw new KernelException($"The query string parameter '{parameterStyle}' serialization style is not supported.");
            }

            var node = OpenApiTypeConverter.Convert(parameter.Name, parameter.Type, argument);

            // Serializing the parameter and adding it to the query string if there's an argument for it.
            segments.Add(serializer.Invoke(parameter, node));
        }

        return string.Join("&", segments);
    }

    #region private

    /// <summary>
    /// Builds operation path.
    /// </summary>
    /// <param name="pathTemplate">The original path template.</param>
    /// <param name="arguments">The operation arguments.</param>
    /// <returns>The path.</returns>
    private string BuildPath(string pathTemplate, IDictionary<string, object?> arguments)
    {
        var parameters = this.Parameters.Where(p => p.Location == RestApiOperationParameterLocation.Path);

        foreach (var parameter in parameters)
        {
            if (!arguments.TryGetValue(parameter.Name, out object? argument) || argument is null)
            {
                // Throw an exception if the parameter is a required one but no value is provided.
                if (parameter.IsRequired)
                {
                    throw new KernelException($"No argument is provided for the '{parameter.Name}' required parameter of the operation - '{this.Id}'.");
                }

                // Skipping not required parameter if no argument provided for it.
                continue;
            }

            var parameterStyle = parameter.Style ?? RestApiOperationParameterStyle.Simple;

            if (!s_parameterSerializers.TryGetValue(parameterStyle, out var serializer))
            {
                throw new KernelException($"The path parameter '{parameterStyle}' serialization style is not supported.");
            }

            var node = OpenApiTypeConverter.Convert(parameter.Name, parameter.Type, argument);

            // Serializing the parameter and adding it to the path.
            pathTemplate = pathTemplate.Replace($"{{{parameter.Name}}}", HttpUtility.UrlEncode(serializer.Invoke(parameter, node)));
        }

        return pathTemplate;
    }

    /// <summary>
    /// Returns operation server Url.
    /// </summary>
    /// <param name="serverUrlOverride">Override for REST API operation server url.</param>
    /// <param name="apiHostUrl">The URL of REST API host.</param>
    /// <param name="arguments">The operation arguments.</param>
    /// <returns>The operation server url.</returns>
    private Uri GetServerUrl(Uri? serverUrlOverride, Uri? apiHostUrl, IDictionary<string, object?> arguments)
    {
        string serverUrlString;

        if (serverUrlOverride is not null)
        {
            serverUrlString = serverUrlOverride.AbsoluteUri;
        }
        else if (this.Server.Url is not null)
        {
            serverUrlString = this.Server.Url;
            foreach (var variable in this.Server.Variables)
            {
                arguments.TryGetValue(variable.Key, out object? value);
                string? strValue = value as string;
                if (strValue is not null && variable.Value.IsValid(strValue))
                {
                    serverUrlString = serverUrlString.Replace($"{{{variable.Key}}}", strValue);
                }
                else if (variable.Value.Default is not null)
                {
                    serverUrlString = serverUrlString.Replace($"{{{variable.Key}}}", variable.Value.Default);
                }
                else
                {
                    throw new KernelException($"No value provided for the '{variable.Key}' server variable of the operation - '{this.Id}'.");
                }
            }
        }
        else
        {
            serverUrlString =
                apiHostUrl?.AbsoluteUri ??
                throw new InvalidOperationException($"Server url is not defined for operation {this.Id}");
        }

        // Make sure base url ends with trailing slash
        if (!serverUrlString.EndsWith("/", StringComparison.OrdinalIgnoreCase))
        {
            serverUrlString += "/";
        }

        return new Uri(serverUrlString);
    }

    private static readonly Dictionary<RestApiOperationParameterStyle, Func<RestApiOperationParameter, JsonNode, string>> s_parameterSerializers = new()
    {
        { RestApiOperationParameterStyle.Simple, SimpleStyleParameterSerializer.Serialize },
        { RestApiOperationParameterStyle.Form, FormStyleParameterSerializer.Serialize },
        { RestApiOperationParameterStyle.SpaceDelimited, SpaceDelimitedStyleParameterSerializer.Serialize },
        { RestApiOperationParameterStyle.PipeDelimited, PipeDelimitedStyleParameterSerializer.Serialize }
    };

    # endregion
}

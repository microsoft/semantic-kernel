// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
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
    public string? Id { get; }

    /// <summary>
    /// The operation description.
    /// </summary>
    public string? Description
    {
        get => this._description;
        set
        {
            this._freezable.ThrowIfFrozen();
            this._description = value;
        }
    }

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
    public IList<RestApiServer> Servers { get; private set; }

    /// <summary>
    ///  Path level servers.
    /// </summary>
    public IList<RestApiServer> PathServers { get; init; }

    /// <summary>
    /// Operation level servers.
    /// </summary>
    public IList<RestApiServer> OperationServers { get; init; }

    /// <summary>
    /// The security requirements.
    /// </summary>
    public IList<RestApiSecurityRequirement> SecurityRequirements { get; private set; }

    /// <summary>
    /// The operation parameters.
    /// </summary>
    public IList<RestApiParameter> Parameters { get; private set; }

    /// <summary>
    /// The list of possible operation responses.
    /// </summary>
    public IDictionary<string, RestApiExpectedResponse> Responses { get; private set; }

    /// <summary>
    /// The operation payload.
    /// </summary>
    public RestApiPayload? Payload { get; }

    /// <summary>
    /// Additional unstructured metadata about the operation.
    /// </summary>
    public IDictionary<string, object?> Extensions
    {
        get => this._extensions;
        init => this._extensions = value;
    }

    /// <summary>
    /// Creates an instance of a <see cref="RestApiOperation"/> class.
    /// </summary>
    /// <param name="id">The operation identifier.</param>
    /// <param name="servers">The servers.</param>
    /// <param name="path">The operation path.</param>
    /// <param name="method">The operation method.</param>
    /// <param name="description">The operation description.</param>
    /// <param name="parameters">The operation parameters.</param>
    /// <param name="responses">The operation responses.</param>
    /// <param name="securityRequirements">The operation security requirements.</param>
    /// <param name="payload">The operation payload.</param>
    /// <param name="pathServers">The path servers.</param>
    /// <param name="operationServers">The operation servers.</param>
    internal RestApiOperation(
        string? id,
        IList<RestApiServer> servers,
        string path,
        HttpMethod method,
        string? description,
        IList<RestApiParameter> parameters,
        IDictionary<string, RestApiExpectedResponse> responses,
        IList<RestApiSecurityRequirement> securityRequirements,
        RestApiPayload? payload = null,
        IList<RestApiServer>? pathServers = null,
        IList<RestApiServer>? operationServers = null)
    {
        this.Id = id;
        this.Servers = servers;
        this.Path = path;
        this.Method = method;
        this.Description = description;
        this.Parameters = parameters;
        this.Responses = responses ?? new Dictionary<string, RestApiExpectedResponse>();
        this.SecurityRequirements = securityRequirements;
        this.Payload = payload;
        this.PathServers = pathServers ?? new List<RestApiServer>();
        this.OperationServers = operationServers ?? new List<RestApiServer>();
    }

    /// <summary>
    /// Builds operation Url.
    /// </summary>
    /// <param name="arguments">The operation arguments.</param>
    /// <param name="serverUrlOverride">Override for REST API operation server url.</param>
    /// <param name="apiHostUrl">The URL of REST API host.</param>
    /// <returns>The operation Url.</returns>
    internal Uri BuildOperationUrl(IDictionary<string, object?> arguments, Uri? serverUrlOverride = null, Uri? apiHostUrl = null)
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
    internal IDictionary<string, string> BuildHeaders(IDictionary<string, object?> arguments)
    {
        var headers = new Dictionary<string, string>();

        var parameters = this.Parameters.Where(p => p.Location == RestApiParameterLocation.Header);

        foreach (var parameter in parameters)
        {
            var argument = this.GetArgumentForParameter(arguments, parameter);
            if (argument == null)
            {
                // Skipping not required parameter if no argument provided for it.    
                continue;
            }

            var parameterStyle = parameter.Style ?? RestApiParameterStyle.Simple;

            if (!s_parameterSerializers.TryGetValue(parameterStyle, out var serializer))
            {
                throw new KernelException($"The headers parameter '{parameterStyle}' serialization style is not supported.");
            }

            var node = OpenApiTypeConverter.Convert(parameter.Name, parameter.Type, argument, parameter.Schema);

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
    internal string BuildQueryString(IDictionary<string, object?> arguments)
    {
        var segments = new List<string>();

        var parameters = this.Parameters.Where(p => p.Location == RestApiParameterLocation.Query);

        foreach (var parameter in parameters)
        {
            var argument = this.GetArgumentForParameter(arguments, parameter);
            if (argument == null)
            {
                // Skipping not required parameter if no argument provided for it.    
                continue;
            }

            var parameterStyle = parameter.Style ?? RestApiParameterStyle.Form;

            if (!s_parameterSerializers.TryGetValue(parameterStyle, out var serializer))
            {
                throw new KernelException($"The query string parameter '{parameterStyle}' serialization style is not supported.");
            }

            var node = OpenApiTypeConverter.Convert(parameter.Name, parameter.Type, argument, parameter.Schema);

            // Serializing the parameter and adding it to the query string if there's an argument for it.
            segments.Add(serializer.Invoke(parameter, node));
        }

        return string.Join("&", segments);
    }

    /// <summary>
    /// Makes the current instance unmodifiable.
    /// </summary>
    internal void Freeze()
    {
        this._freezable.Freeze();
        this.Payload?.Freeze();

        this.Parameters = new ReadOnlyCollection<RestApiParameter>(this.Parameters);
        foreach (var parameter in this.Parameters)
        {
            parameter.Freeze();
        }

        this.Servers = new ReadOnlyCollection<RestApiServer>(this.Servers);
        foreach (var server in this.Servers)
        {
            server.Freeze();
        }

        this.SecurityRequirements = new ReadOnlyCollection<RestApiSecurityRequirement>(this.SecurityRequirements);
        foreach (var securityRequirement in this.SecurityRequirements)
        {
            securityRequirement.Freeze();
        }

        this.Responses = new ReadOnlyDictionary<string, RestApiExpectedResponse>(this.Responses);

        this._extensions = new ReadOnlyDictionary<string, object?>(this._extensions);
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
        var parameters = this.Parameters.Where(p => p.Location == RestApiParameterLocation.Path);

        foreach (var parameter in parameters)
        {
            var argument = this.GetArgumentForParameter(arguments, parameter);
            if (argument == null)
            {
                // Skipping not required parameter if no argument provided for it.    
                continue;
            }

            var parameterStyle = parameter.Style ?? RestApiParameterStyle.Simple;

            if (!s_parameterSerializers.TryGetValue(parameterStyle, out var serializer))
            {
                throw new KernelException($"The path parameter '{parameterStyle}' serialization style is not supported.");
            }

            var node = OpenApiTypeConverter.Convert(parameter.Name, parameter.Type, argument, parameter.Schema);

            // Serializing the parameter and adding it to the path.
            pathTemplate = pathTemplate.Replace($"{{{parameter.Name}}}", HttpUtility.UrlEncode(serializer.Invoke(parameter, node)));
        }

        return pathTemplate;
    }

    private object? GetArgumentForParameter(IDictionary<string, object?> arguments, RestApiParameter parameter)
    {
        // Try to get the parameter value by the argument name.
        if (!string.IsNullOrEmpty(parameter.ArgumentName) &&
            arguments.TryGetValue(parameter.ArgumentName!, out object? argument) &&
            argument is not null)
        {
            return argument;
        }

        // Try to get the parameter value by the parameter name.
        if (arguments.TryGetValue(parameter.Name, out argument) &&
            argument is not null)
        {
            return argument;
        }

        if (parameter.IsRequired)
        {
            throw new KernelException($"No argument '{parameter.ArgumentName ?? parameter.Name}' is provided for the '{parameter.Name}' required parameter of the operation - '{this.Id}'.");
        }

        return null;
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
        else if (this.Servers is { Count: > 0 } servers && servers[0].Url is { } url)
        {
            serverUrlString = url;

            foreach (var variable in servers[0].Variables)
            {
                var variableName = variable.Key;

                // Try to get the variable value by the argument name.
                if (!string.IsNullOrEmpty(variable.Value.ArgumentName) &&
                    arguments.TryGetValue(variable.Value.ArgumentName!, out object? value) &&
                    value is string { } argStrValue && variable.Value.IsValid(argStrValue))
                {
                    serverUrlString = url.Replace($"{{{variableName}}}", argStrValue);
                }
                // Try to get the variable value by the variable name.
                else if (arguments.TryGetValue(variableName, out value) &&
                    value is string { } strValue &&
                    variable.Value.IsValid(strValue))
                {
                    serverUrlString = url.Replace($"{{{variableName}}}", strValue);
                }
                // Use the default value if no argument is provided.
                else if (variable.Value.Default is not null)
                {
                    serverUrlString = url.Replace($"{{{variableName}}}", variable.Value.Default);
                }
                // Throw an exception if there's no value for the variable.
                else
                {
                    throw new KernelException($"No argument '{variable.Value.ArgumentName ?? variableName}' provided for the '{variableName}' server variable of the operation - '{this.Id}'.");
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

    private static readonly Dictionary<RestApiParameterStyle, Func<RestApiParameter, JsonNode, string>> s_parameterSerializers = new()
    {
        { RestApiParameterStyle.Simple, SimpleStyleParameterSerializer.Serialize },
        { RestApiParameterStyle.Form, FormStyleParameterSerializer.Serialize },
        { RestApiParameterStyle.SpaceDelimited, SpaceDelimitedStyleParameterSerializer.Serialize },
        { RestApiParameterStyle.PipeDelimited, PipeDelimitedStyleParameterSerializer.Serialize }
    };

    private IDictionary<string, object?> _extensions = s_emptyDictionary;
    private readonly Freezable _freezable = new();
    private string? _description;

    #endregion
}

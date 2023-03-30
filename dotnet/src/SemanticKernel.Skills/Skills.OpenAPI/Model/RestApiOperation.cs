// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.RegularExpressions;
using Microsoft.SemanticKernel.Skills.OpenAPI.Rest;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Model;

/// <summary>
/// The REST API operation.
/// </summary>
internal class RestApiOperation
{
    /// <summary>
    /// An artificial parameter that is added to be able to override RESP API operation server url.
    /// </summary>
    internal const string ServerUrlArgumentName = "server-url";

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
    public string ServerUrl { get; }

    /// <summary>
    /// The operation headers.
    /// </summary>
    public IDictionary<string, string> Headers { get; private set; } = new Dictionary<string, string>();

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
    /// <param name="payload">The operation payload.</param>
    public RestApiOperation(string id, string serverUrl, string path, HttpMethod method, string description, IList<RestApiOperationParameter> parameters, RestApiOperationPayload? payload = null)
    {
        this.Id = id;
        this.ServerUrl = serverUrl;
        this.Path = path;
        this.Method = method;
        this.Description = description;
        this.Parameters = parameters;
        this.Payload = payload;
    }

    /// <summary>
    /// Builds operation Url.
    /// </summary>
    /// <param name="arguments">The operation arguments.</param>
    /// <returns>The operation Url.</returns>
    public Uri BuildOperationUrl(IDictionary<string, string> arguments)
    {
        var path = this.ReplacePathParameters(this.Path, arguments);

        path = this.AddQueryString(path, arguments);

        //Override defined server url - https://api.example.com/v1 by the one from arguments. 
        if (!arguments.TryGetValue(ServerUrlArgumentName, out var serverUrl))
        {
            serverUrl = this.ServerUrl;
        }

        return new Uri(new Uri(serverUrl, UriKind.Absolute), path);
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
            var parameterMetadata = this.Parameters.First(p => p.Type == RestApiOperationParameterType.Path && p.Name == parameterName);
            if (parameterMetadata?.DefaultValue == null)
            {
                throw new RestApiOperationException($"No argument found for parameter - '{parameterName}' for operation - '{this.Id}'");
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
        var builder = new StringBuilder();

        var queryStringParameters = this.Parameters.Where(p => p.Type == RestApiOperationParameterType.Query);

        foreach (var parameter in queryStringParameters)
        {
            //Add the parameter to the query string if there's an argument for it
            if (arguments.TryGetValue(parameter.Name, out var argument))
            {
                builder.AppendJoin('&', $"{parameter.Name}={argument}");
                continue;
            }

            //Add the parameter to the query string if there's a default value for it.
            if (!string.IsNullOrEmpty(parameter.DefaultValue))
            {
                builder.AppendJoin('&', $"{parameter.Name}={parameter.DefaultValue}");
                continue;
            }

            //Throw an exception if the parameter is a required one but no value is provided.
            if (parameter.IsRequired)
            {
                throw new RestApiOperationException($"No argument found for required query string parameter - '{parameter.Name}' for operation - '{this.Id}'");
            }
        }

        var queryString = builder.ToString();

        return string.IsNullOrEmpty(queryString) ? path : $"{path}?{queryString}";
    }

    private static readonly Regex s_urlParameterMatch = new Regex(@"\{([\w-]+)\}");

    # endregion
}

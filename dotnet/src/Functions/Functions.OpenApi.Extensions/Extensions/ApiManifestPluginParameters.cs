// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Plugins.OpenApi.Extensions;

/// <summary>
/// API manifest plugin parameters.
/// </summary>
public sealed class ApiManifestPluginParameters
{
    /// <summary>
    /// Gets the HTTP client to be used in plugin initialization phase.
    /// </summary>
    public HttpClient? HttpClient { get; init; }

    /// <summary>
    /// Gets the user agent to be used in plugin initialization phase.
    /// </summary>
    public string? UserAgent { get; init; }

    /// <summary>
    /// Gets the options used to validate the URLs of the OpenAPI documents loaded in plugin initialization phase.
    /// If <see langword="null"/>, the default policy is applied: only HTTPS URLs that resolve to public addresses are allowed.
    /// </summary>
    public RestApiOperationServerUrlValidationOptions? ServerUrlValidationOptions { get; init; }

    /// <summary>
    /// A map of function execution parameters, where the key is the api dependency key from api manifest
    /// and the value is OpenApiFunctionExecutionParameters specific to that dependency.
    /// </summary>
    public Dictionary<string, OpenApiFunctionExecutionParameters>? FunctionExecutionParameters { get; init; }

    /// <summary>
    /// Initializes a new instance of the <see cref="ApiManifestPluginParameters"/> class.
    /// </summary>
    /// <param name="httpClient">Http client to be used in plugin initialization phase.</param>
    /// <param name="userAgent">User agent to be used in plugin initialization phase.</param>
    /// <param name="functionExecutionParameters">A map of function execution parameters.</param>
    public ApiManifestPluginParameters(
        HttpClient? httpClient = default,
        string? userAgent = default,
        Dictionary<string, OpenApiFunctionExecutionParameters>? functionExecutionParameters = default
    )
    {
        this.HttpClient = httpClient;
        this.UserAgent = userAgent;
        this.FunctionExecutionParameters = functionExecutionParameters;
    }
}

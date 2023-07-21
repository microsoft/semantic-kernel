// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Extensions;

/// <summary>
/// OpenAPI skill execution parameters.
/// </summary>
public class OpenApiSkillExecutionParameters
{
    /// <summary>
    /// HttpClient to use for sending HTTP requests.
    /// </summary>
    public HttpClient? HttpClient { get; set; }

    /// <summary>
    /// Callback for adding authentication data to HTTP requests.
    /// </summary>
    public AuthenticateRequestAsyncCallback? AuthCallback { get; set; }

    /// <summary>
    /// Override for RESP API operation server url.
    /// </summary>
    public Uri? ServerUrlOverride { get; set; }

    /// <summary>
    /// Flag indicating whether to ignore non-compliant errors or not.
    /// If set to true, the operation execution will not throw exceptions for non-compliant documents.
    /// Please note that enabling this option may result in incomplete or inaccurate execution results.
    /// </summary>
    public bool IgnoreNonCompliantErrors { get; set; }

    /// <summary>
    /// Optional user agent header value.
    /// </summary>
    public string? UserAgent { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenApiSkillExecutionParameters"/> class.
    /// </summary>
    /// <param name="httpClient">The HttpClient to use for sending HTTP requests.</param>
    /// <param name="authCallback">The callback for adding authentication data to HTTP requests.</param>
    /// <param name="serverUrlOverride">The override for the RESP API operation server URL.</param>
    /// <param name="userAgent">Optional user agent header value.</param>
    /// <param name="ignoreNonCompliantErrors">A flag indicating whether to ignore non-compliant errors or not
    /// If set to true, the operation execution will not throw exceptions for non-compliant documents.
    /// Please note that enabling this option may result in incomplete or inaccurate execution results.</param>
    public OpenApiSkillExecutionParameters(
        HttpClient? httpClient = null,
        AuthenticateRequestAsyncCallback? authCallback = null,
        Uri? serverUrlOverride = null,
        string? userAgent = MicrosoftDiagnostics.HttpUserAgent,
        bool ignoreNonCompliantErrors = false)
    {
        this.HttpClient = httpClient;
        this.AuthCallback = authCallback;
        this.ServerUrlOverride = serverUrlOverride;
        this.UserAgent = userAgent;
        this.IgnoreNonCompliantErrors = ignoreNonCompliantErrors;
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// OpenAI function execution parameters
/// </summary>
public class OpenAIFunctionExecutionParameters : OpenApiFunctionExecutionParameters
{
    /// <summary>
    /// Callback for adding Open AI authentication data to HTTP requests.
    /// </summary>
    public new OpenAIAuthenticateRequestAsyncCallback? AuthCallback { get; set; }

    /// <inheritdoc/>
    public OpenAIFunctionExecutionParameters(
        HttpClient? httpClient = null,
        OpenAIAuthenticateRequestAsyncCallback? authCallback = null,
        Uri? serverUrlOverride = null,
        string userAgent = HttpHeaderValues.UserAgent,
        bool ignoreNonCompliantErrors = false,
        bool enableDynamicOperationPayload = false,
        bool enablePayloadNamespacing = false) : base(httpClient, null, serverUrlOverride, userAgent, ignoreNonCompliantErrors, enableDynamicOperationPayload, enablePayloadNamespacing)
    {
        this.AuthCallback = authCallback;
    }
}

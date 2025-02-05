// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net;

namespace Microsoft.SemanticKernel.ChatCompletion;

public sealed class DefaultFallbackEvaluator : FallbackEvaluator
{
    private static readonly List<HttpStatusCode> s_defaultFallbackStatusCodes = new()
    {
        HttpStatusCode.InternalServerError,
        HttpStatusCode.NotImplemented,
        HttpStatusCode.BadGateway,
        HttpStatusCode.ServiceUnavailable,
        HttpStatusCode.GatewayTimeout
    };

    public List<HttpStatusCode>? FallbackStatusCodes { get; set; }

    public bool FallbackOnUnavailableStatusCode { get; set; } = false;

    public bool FallbackOnUnknownException { get; set; } = false;

    public override bool ShouldFallbackToNextClient(ShouldFallbackContext context)
    {
        HttpStatusCode? statusCode = null;

        if (context.Exception is HttpOperationException operationException)
        {
            statusCode = operationException.StatusCode;
        }
#if NET
        else if (context.Exception is System.Net.Http.HttpRequestException httpRequestException)
        {
            statusCode = httpRequestException.StatusCode;
        }
#endif
        else
        {
            if (this.FallbackOnUnknownException)
            {
                return true;
            }

            throw new InvalidOperationException($"Unsupported exception type: {context.Exception.GetType()}. Please provide a corresponding fallback evaluator that can handle this exception type.");
        }

        if (statusCode is null)
        {
            return this.FallbackOnUnavailableStatusCode;
        }

        return (this.FallbackStatusCodes ?? s_defaultFallbackStatusCodes).Contains(statusCode!.Value);
    }
}

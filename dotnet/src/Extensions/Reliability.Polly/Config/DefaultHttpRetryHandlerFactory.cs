// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Config;

namespace Microsoft.SemanticKernel.Reliability.Polly.Config;

public class DefaultHttpRetryHandlerFactory : HttpHandlerFactory<DefaultHttpRetryHandler>
{
    public DefaultHttpRetryHandlerFactory(HttpRetryConfig? config = null)
    {
        this.Config = config;
    }

    public HttpRetryConfig? Config { get; }
}

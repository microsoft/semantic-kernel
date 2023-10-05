// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Http;
using Polly;

namespace Microsoft.SemanticKernel.Reliability.Polly;

/// <summary>
/// Customizable PollyHttpHandlerFactory that will create handlers with the provided policy.
/// </summary>
public class PollyHttpRetryHandlerFactory : HttpHandlerFactory<PollyHttpRetryHandler>
{
    private readonly AsyncPolicy<HttpResponseMessage>? _typedAsyncPolicy;
    private readonly AsyncPolicy? _asyncPolicy;
    private readonly ResiliencePipeline<HttpResponseMessage>? _typedResiliencePipeline;
    private readonly ResiliencePipeline? _resiliencePipeline;

    /// <summary>
    /// Creates a new instance of <see cref="PollyHttpRetryHandler"/>.
    /// </summary>
    /// <param name="typedAsyncPolicy">HttpResponseMessage typed AsyncPolicy</param> dedicated for <see cref="HttpResponseMessage"/> typed policies.
    [Obsolete("Use one of the constructors that takes a ResiliencePipeline instead (https://www.pollydocs.org/migration-v8.html).")]
    public PollyHttpRetryHandlerFactory(AsyncPolicy<HttpResponseMessage> typedAsyncPolicy)
    {
        Verify.NotNull(typedAsyncPolicy);

        this._typedAsyncPolicy = typedAsyncPolicy;
    }

    /// <summary>
    /// Creates a new instance of <see cref="PollyHttpRetryHandler"/> dedicated for non-typed policies.
    /// </summary>
    /// <param name="asyncPolicy">A non-typed AsyncPolicy</param>
    [Obsolete("Use one of the constructors that takes a ResiliencePipeline instead (https://www.pollydocs.org/migration-v8.html).")]
    public PollyHttpRetryHandlerFactory(AsyncPolicy asyncPolicy)
    {
        Verify.NotNull(asyncPolicy);

        this._asyncPolicy = asyncPolicy;
    }

    /// <summary>
    /// Creates a new instance of <see cref="PollyHttpRetryHandler"/>.
    /// </summary>
    /// <param name="typedResiliencePipeline">HttpResponseMessage typed ResiliencePipeline</param> dedicated for <see cref="HttpResponseMessage"/> typed strategies.
    public PollyHttpRetryHandlerFactory(ResiliencePipeline<HttpResponseMessage> typedResiliencePipeline)
    {
        Verify.NotNull(typedResiliencePipeline);

        this._typedResiliencePipeline = typedResiliencePipeline;
    }

    /// <summary>
    /// Creates a new instance of <see cref="PollyHttpRetryHandler"/> dedicated for non-typed strategies.
    /// </summary>
    /// <param name="resiliencePipeline">A non-typed ResiliencePipeline</param>
    public PollyHttpRetryHandlerFactory(ResiliencePipeline resiliencePipeline)
    {
        Verify.NotNull(resiliencePipeline);

        this._resiliencePipeline = resiliencePipeline;
    }

    /// <summary>
    /// Creates a new instance of <see cref="DefaultHttpRetryHandler"/> with the default configuration.
    /// </summary>
    /// <param name="loggerFactory">Logger factory</param>
    /// <returns>Returns the created handler</returns>
    public override DelegatingHandler Create(ILoggerFactory? loggerFactory = null)
    {
        if (this._typedAsyncPolicy is not null)
        {
            return new PollyHttpRetryHandler(this._typedAsyncPolicy);
        }

        if (this._asyncPolicy is not null)
        {
            return new PollyHttpRetryHandler(this._asyncPolicy);
        }

        if (this._typedResiliencePipeline is not null)
        {
            return new PollyHttpRetryHandler(this._typedResiliencePipeline);
        }

        return new PollyHttpRetryHandler(this._resiliencePipeline!);
    }
}

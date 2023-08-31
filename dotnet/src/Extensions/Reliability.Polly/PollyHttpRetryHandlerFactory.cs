// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Config;
using Microsoft.SemanticKernel.Diagnostics;
using Polly;

namespace Microsoft.SemanticKernel.Reliability.Polly;

/// <summary>
/// Customizable PollyHttpHandlerFactory that will create handlers with the provided policy.
/// </summary>
public class PollyHttpRetryHandlerFactory : HttpHandlerFactory<PollyHttpRetryHandler>
{
    private readonly AsyncPolicy<HttpResponseMessage>? _typedAsyncPolicy;
    private readonly AsyncPolicy? _asyncPolicy;

    /// <summary>
    /// Creates a new instance of <see cref="PollyHttpRetryHandler"/>.
    /// </summary>
    /// <param name="typedAsyncPolicy">HttpResponseMessage typed AsyncPolicy</param> dedicated for <see cref="HttpResponseMessage"/> typed policies.
    /// <param name="loggerFactory">Logger factory</param>
    public PollyHttpRetryHandlerFactory(AsyncPolicy<HttpResponseMessage> typedAsyncPolicy, ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(typedAsyncPolicy);

        this._typedAsyncPolicy = typedAsyncPolicy;
    }

    /// <summary>
    /// Creates a new instance of <see cref="PollyHttpRetryHandler"/> dedicated for non-typed policies.
    /// </summary>
    /// <param name="asyncPolicy">A non-typed AsyncPolicy</param>
    /// <param name="loggerFactory">Logger factory</param>
    public PollyHttpRetryHandlerFactory(AsyncPolicy asyncPolicy, ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(asyncPolicy);

        this._asyncPolicy = asyncPolicy;
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
            return new PollyHttpRetryHandler(this._typedAsyncPolicy, loggerFactory);
        }

        return new PollyHttpRetryHandler(this._asyncPolicy!, loggerFactory);
    }
}

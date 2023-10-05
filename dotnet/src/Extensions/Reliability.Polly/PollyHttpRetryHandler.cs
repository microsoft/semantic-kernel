// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;
using Polly;

namespace Microsoft.SemanticKernel.Reliability.Polly;

/// <summary>
/// Customizable PollyHttpHandler that will follow the provided policy.
/// </summary>
public class PollyHttpRetryHandler : DelegatingHandler
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
    public PollyHttpRetryHandler(AsyncPolicy<HttpResponseMessage> typedAsyncPolicy)
    {
        Verify.NotNull(typedAsyncPolicy);

        this._typedAsyncPolicy = typedAsyncPolicy;
    }

    /// <summary>
    /// Creates a new instance of <see cref="PollyHttpRetryHandler"/> dedicated for non-typed policies.
    /// </summary>
    /// <param name="asyncPolicy">A non-typed AsyncPolicy</param>
    [Obsolete("Use one of the constructors that takes a ResiliencePipeline instead (https://www.pollydocs.org/migration-v8.html).")]
    public PollyHttpRetryHandler(AsyncPolicy asyncPolicy)
    {
        Verify.NotNull(asyncPolicy);

        this._asyncPolicy = asyncPolicy;
    }

    /// <summary>
    /// Creates a new instance of <see cref="PollyHttpRetryHandler"/>.
    /// </summary>
    /// <param name="typedResiliencePipeline">HttpResponseMessage typed ResiliencePipeline</param> dedicated for <see cref="HttpResponseMessage"/> typed strategies.
    public PollyHttpRetryHandler(ResiliencePipeline<HttpResponseMessage> typedResiliencePipeline)
    {
        Verify.NotNull(typedResiliencePipeline);

        this._typedResiliencePipeline = typedResiliencePipeline;
    }

    /// <summary>
    /// Creates a new instance of <see cref="PollyHttpRetryHandler"/> dedicated for non-typed strategies.
    /// </summary>
    /// <param name="resiliencePipeline">A non-typed ResiliencePipeline</param>
    public PollyHttpRetryHandler(ResiliencePipeline resiliencePipeline)
    {
        Verify.NotNull(resiliencePipeline);

        this._resiliencePipeline = resiliencePipeline;
    }

    /// <inheritdoc/>
    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();

        if (this._typedAsyncPolicy is not null)
        {
            return await this._typedAsyncPolicy.ExecuteAsync(async (cancelToken) =>
            {
                var response = await base.SendAsync(request, cancelToken).ConfigureAwait(false);
                return response;
            }, cancellationToken).ConfigureAwait(false);
        }

        if (this._asyncPolicy is not null)
        {
            return await this._asyncPolicy.ExecuteAsync(async (cancelToken) =>
            {
                var response = await base.SendAsync(request, cancelToken).ConfigureAwait(false);
                return response;
            }, cancellationToken).ConfigureAwait(false);
        }

        if (this._typedResiliencePipeline is not null)
        {
            return await this._typedResiliencePipeline.ExecuteAsync(async (cancelToken) =>
            {
                var response = await base.SendAsync(request, cancelToken).ConfigureAwait(false);
                return response;
            }, cancellationToken).ConfigureAwait(false);
        }

        return await this._resiliencePipeline!.ExecuteAsync(async (cancelToken) =>
        {
            var response = await base.SendAsync(request, cancelToken).ConfigureAwait(false);
            return response;
        }, cancellationToken).ConfigureAwait(false);
    }
}

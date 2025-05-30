// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel.Primitives;
using System.Collections.Generic;
using System.Threading.Tasks;
using Azure.Core;
using Azure.Core.Pipeline;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// RoutingPolicy for managing Foundry Workflows.
/// </summary>
public class HttpPipelineRoutingPolicy : HttpPipelinePolicy
{
    private readonly Uri _endpoint;
    private readonly string _apiVersion;

    /// <summary>
    /// Initializes a new instance of the <see cref="HttpPipelineRoutingPolicy"/> class.
    /// </summary>
    /// <param name="endpoint">The endpoint URI.</param>
    /// <param name="apiVersion">The API version.</param>
    public HttpPipelineRoutingPolicy(Uri endpoint, string apiVersion)
    {
        this._endpoint = endpoint ?? throw new ArgumentNullException(nameof(endpoint));
        this._apiVersion = apiVersion ?? throw new ArgumentNullException(nameof(apiVersion));
    }

    /// <summary>
    /// Processes the HTTP message and routes it as needed.
    /// </summary>
    /// <param name="message">The HTTP message.</param>
    /// <param name="pipeline">The pipeline policies.</param>
    public override void Process(HttpMessage message, ReadOnlyMemory<HttpPipelinePolicy> pipeline)
    {
        this.Process(message);

        ProcessNext(message, pipeline);
    }

    /// <summary>
    /// Asynchronously processes the HTTP message and routes it as needed.
    /// </summary>
    /// <param name="message">The HTTP message.</param>
    /// <param name="pipeline">The pipeline policies.</param>
    /// <returns>A <see cref="ValueTask"/> representing the asynchronous operation.</returns>
    public override ValueTask ProcessAsync(HttpMessage message, ReadOnlyMemory<HttpPipelinePolicy> pipeline)
    {
        this.Process(message);

        return ProcessNextAsync(message, pipeline);
    }

    /// <summary>
    /// Processes the HTTP message and updates its URI for routing.
    /// </summary>
    /// <param name="message">The HTTP message.</param>
    public void Process(HttpMessage message)
    {
        if (message.Request.Uri is null)
        {
            throw new ArgumentException(nameof(message.Request.Uri));
        }
        else if (message.Request.Uri.ToUri().IsLoopback)
        {
            message.Request.Uri.Reset(new Uri(string.Format($"{this._endpoint.ToString().TrimEnd('/')}/{message.Request.Uri.ToUri().AbsolutePath.TrimStart('/')}?api-version={this._apiVersion}")));
        }

        message.Request.Uri.Reset(message.Request.Uri.ToUri().Reroute(apiVersion: this._apiVersion, isWorkflow: message.Request.Content!.IsWorkflow()));
    }
}

/// <summary>
/// Pipeline policy for routing requests in the Foundry pipeline.
/// </summary>
public class PipelineRoutingPolicy : PipelinePolicy
{
    private readonly Uri _endpoint;
    private readonly string _apiVersion;

    /// <summary>
    /// Initializes a new instance of the <see cref="PipelineRoutingPolicy"/> class.
    /// </summary>
    /// <param name="endpoint">The endpoint URI.</param>
    /// <param name="apiVersion">The API version.</param>
    public PipelineRoutingPolicy(Uri endpoint, string apiVersion)
    {
        this._endpoint = endpoint ?? throw new ArgumentNullException(nameof(endpoint));
        this._apiVersion = apiVersion ?? throw new ArgumentNullException(nameof(apiVersion));
    }

    /// <summary>
    /// Processes the pipeline message and routes it as needed.
    /// </summary>
    /// <param name="message">The pipeline message.</param>
    /// <param name="pipeline">The pipeline policies.</param>
    /// <param name="currentIndex">The current index in the pipeline.</param>
    public override void Process(PipelineMessage message, IReadOnlyList<PipelinePolicy> pipeline, int currentIndex)
    {
        this.ProcessRequest(message.Request);
        ProcessNext(message, pipeline, currentIndex);
    }

    /// <summary>
    /// Asynchronously processes the pipeline message and routes it as needed.
    /// </summary>
    /// <param name="message">The pipeline message.</param>
    /// <param name="pipeline">The pipeline policies.</param>
    /// <param name="currentIndex">The current index in the pipeline.</param>
    /// <returns>A <see cref="ValueTask"/> representing the asynchronous operation.</returns>
    public override async ValueTask ProcessAsync(PipelineMessage message, IReadOnlyList<PipelinePolicy> pipeline, int currentIndex)
    {
        this.ProcessRequest(message.Request);
        await ProcessNextAsync(message, pipeline, currentIndex).ConfigureAwait(false);
    }

    private void ProcessRequest(PipelineRequest request)
    {
        if (request.Uri is null)
        {
            throw new InvalidOperationException($"{nameof(request.Uri)} cannot be null");
        }
        else if (request.Uri.IsLoopback)
        {
            request.Uri = new Uri(string.Format($"{this._endpoint.ToString().TrimEnd('/')}/{request.Uri.AbsolutePath.TrimStart('/')}?api-version={this._apiVersion}"));
        }

        request.Uri = request.Uri.Reroute(apiVersion: this._apiVersion, isWorkflow: request.Content!.IsWorkflow());
    }
}

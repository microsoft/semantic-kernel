// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using System;
using System.ClientModel.Primitives;
using System.Reflection;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Helper class to inject headers into Azure SDK HTTP pipeline
/// </summary>
internal sealed class AddHeaderRequestPolicy(string headerName, string headerValue) : HttpPipelineSynchronousPolicy
{
    private readonly string _headerName = headerName;
    private readonly string _headerValue = headerValue;

    public override void OnSendingRequest(PipelineMessage message)
    {
        message.Request.Headers.Add(this._headerName, this._headerValue);
    }
}

internal abstract class HttpPipelinePolicy : PipelinePolicy
{
    /// <summary>
    /// Invokes the next <see cref="HttpPipelinePolicy"/> in the <paramref name="pipeline"/>.
    /// </summary>
    /// <param name="message">The <see cref="PipelineMessage"/> next policy would be applied to.</param>
    /// <param name="pipeline">The set of <see cref="HttpPipelinePolicy"/> to execute after next one.</param>
    /// <param name="currentIndex">Current index in the pipeline</param>
    /// <returns>The <see cref="ValueTask"/> representing the asynchronous operation.</returns>
    protected static ValueTask ProcessNextAsync(PipelineMessage message, ReadOnlyMemory<PipelinePolicy> pipeline, int currentIndex)
    {
        return pipeline.Span[0].ProcessAsync(message, pipeline.Slice(1).Span.ToArray(), currentIndex);
    }

    /// <summary>
    /// Invokes the next <see cref="HttpPipelinePolicy"/> in the <paramref name="pipeline"/>.
    /// </summary>
    /// <param name="message">The <see cref="PipelineMessage"/> next policy would be applied to.</param>
    /// <param name="pipeline">The set of <see cref="HttpPipelinePolicy"/> to execute after next one.</param>
    /// <param name="currentIndex">Current index in the pipeline</param>
    protected static void ProcessNext(PipelineMessage message, ReadOnlyMemory<PipelinePolicy> pipeline, int currentIndex)
    {
        pipeline.Span[0].Process(message, pipeline.Slice(1).Span.ToArray(), currentIndex);
    }
}

/// <summary>
/// Represents a <see cref="HttpPipelinePolicy"/> that doesn't do any asynchronous or synchronously blocking operations.
/// </summary>
internal class HttpPipelineSynchronousPolicy : HttpPipelinePolicy
{
    private static readonly Type[] s_onReceivedResponseParameters = new[] { typeof(PipelineMessage) };

    private readonly bool _hasOnReceivedResponse = true;

    /// <summary>
    /// Initializes a new instance of <see cref="HttpPipelineSynchronousPolicy"/>
    /// </summary>
    protected HttpPipelineSynchronousPolicy()
    {
        var onReceivedResponseMethod = GetType().GetMethod(nameof(OnReceivedResponse), BindingFlags.Instance | BindingFlags.Public, null, s_onReceivedResponseParameters, null);
        if (onReceivedResponseMethod != null)
        {
            this._hasOnReceivedResponse = onReceivedResponseMethod.GetBaseDefinition().DeclaringType != onReceivedResponseMethod.DeclaringType;
        }
    }

    /// <inheritdoc />
    public override void Process(PipelineMessage message, IReadOnlyList<PipelinePolicy> pipeline, int currentIndex)
    {
        this.OnSendingRequest(message);
        ProcessNext(message, pipeline, currentIndex);
        this.OnReceivedResponse(message);
    }

    /// <inheritdoc />
    public override ValueTask ProcessAsync(PipelineMessage message, IReadOnlyList<PipelinePolicy> pipeline, int currentIndex)
    {
        if (!this._hasOnReceivedResponse)
        {
            // If OnReceivedResponse was not overridden we can avoid creating a state machine and return the task directly
            this.OnSendingRequest(message);
            return ProcessNextAsync(message, pipeline, currentIndex);
        }

        return this.InnerProcessAsync(message, pipeline, currentIndex);
    }

    private async ValueTask InnerProcessAsync(PipelineMessage message, IReadOnlyList<PipelinePolicy> pipeline, int currentIndex)
    {
        this.OnSendingRequest(message);
        await ProcessNextAsync(message, pipeline, currentIndex).ConfigureAwait(false);
        this.OnReceivedResponse(message);
    }

    /// <summary>
    /// Method is invoked before the request is sent.
    /// </summary>
    /// <param name="message">The <see cref="PipelineMessage" /> containing the request.</param>
    public virtual void OnSendingRequest(PipelineMessage message) { }

    /// <summary>
    /// Method is invoked after the response is received.
    /// </summary>
    /// <param name="message">The <see cref="PipelineMessage" /> containing the response.</param>
    public virtual void OnReceivedResponse(PipelineMessage message) { }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel.Primitives;
using System.Collections.Generic;
using System.Reflection;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

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
        var onReceivedResponseMethod = this.GetType().GetMethod(nameof(OnReceivedResponse), BindingFlags.Instance | BindingFlags.Public, null, s_onReceivedResponseParameters, null);
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

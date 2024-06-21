// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel.Primitives;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Helper class to inject headers into System ClientModel Http pipeline
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

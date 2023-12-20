// Copyright (c) Microsoft. All rights reserved.

using Azure.Core;
using Azure.Core.Pipeline;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Helper class to inject headers into Azure SDK HTTP pipeline
/// </summary>
internal sealed class AddHeaderRequestPolicy(string headerName, string headerValue) : HttpPipelineSynchronousPolicy
{
    private readonly string _headerName = headerName;
    private readonly string _headerValue = headerValue;

    public override void OnSendingRequest(HttpMessage message)
    {
        message.Request.Headers.Add(this._headerName, this._headerValue);
    }
}

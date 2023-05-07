// Copyright (c) Microsoft. All rights reserved.

using Azure.Core;
using Azure.Core.Pipeline;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Helper class to inject headers into Azure SDK HTTP pipeline
/// </summary>
internal sealed class AddHeaderRequestPolicy : HttpPipelineSynchronousPolicy
{
    private readonly string _headerName;
    private readonly string _headerValue;

    public AddHeaderRequestPolicy(string headerName, string headerValue)
    {
        this._headerName = headerName;
        this._headerValue = headerValue;
    }

    public override void OnSendingRequest(HttpMessage message)
    {
        message.Request.Headers.Add(this._headerName, this._headerValue);
    }
}

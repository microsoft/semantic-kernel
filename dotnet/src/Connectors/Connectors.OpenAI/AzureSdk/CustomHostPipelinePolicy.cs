// Copyright (c) Microsoft. All rights reserved.

using System;
using Azure.Core;
using Azure.Core.Pipeline;

namespace Microsoft.SemanticKernel.Connectors.OpenAI.Core.AzureSdk;

internal sealed class CustomHostPipelinePolicy : HttpPipelineSynchronousPolicy
{
    private readonly Uri _endpoint;

    internal CustomHostPipelinePolicy(Uri endpoint)
    {
        this._endpoint = endpoint;
    }

    public override void OnSendingRequest(HttpMessage message)
    {
        // Update current host to provided endpoint
        message.Request?.Uri.Reset(this._endpoint);
    }
}

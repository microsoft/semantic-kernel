// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel.Primitives;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

internal sealed class CustomHostPipelinePolicy : HttpPipelineSynchronousPolicy
{
    private readonly Uri _endpoint;

    internal CustomHostPipelinePolicy(Uri endpoint)
    {
        this._endpoint = endpoint;
    }

    public override void OnSendingRequest(PipelineMessage message)
    {
        // Update current host to provided endpoint
        message.Request.Uri = this._endpoint;
    }
}

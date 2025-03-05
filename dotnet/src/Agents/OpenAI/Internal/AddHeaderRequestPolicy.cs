// Copyright (c) Microsoft. All rights reserved.
using Azure.Core;
using Azure.Core.Pipeline;

namespace Microsoft.SemanticKernel.Agents.OpenAI.Internal;

/// <summary>
/// Helper class to inject headers into Azure SDK HTTP pipeline
/// </summary>
internal sealed class AddHeaderRequestPolicy(string headerName, string headerValue) : HttpPipelineSynchronousPolicy
{
    public override void OnSendingRequest(HttpMessage message) => message.Request.Headers.Add(headerName, headerValue);
}

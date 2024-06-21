// Copyright (c) Microsoft. All rights reserved.

/* Phase 1
Added from OpenAI v1 with adapted logic to the System.ClientModel abstraction
*/

using System.ClientModel.Primitives;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Helper class to inject headers into System ClientModel Http pipeline
/// </summary>
internal sealed class AddHeaderRequestPolicy(string headerName, string headerValue) : PipelineSynchronousPolicy
{
    private readonly string _headerName = headerName;
    private readonly string _headerValue = headerValue;

    public override void OnSendingRequest(PipelineMessage message)
    {
        message.Request.Headers.Add(this._headerName, this._headerValue);
    }
}

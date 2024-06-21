// Copyright (c) Microsoft. All rights reserved.

/* Phase 01
This class was imported and adapted from the System.ClientModel Unit Tests.
https://github.com/Azure/azure-sdk-for-net/blob/main/sdk/core/System.ClientModel/tests/TestFramework/Mocks/MockPipelineMessage.cs
*/

using System.ClientModel.Primitives;
using System.Threading;

namespace SemanticKernel.Connectors.OpenAI.UnitTests;

public class MockPipelineMessage : PipelineMessage
{
#pragma warning disable CA2000 // Dispose objects before losing scope
    public MockPipelineMessage() : this(new MockPipelineRequest())
#pragma warning restore CA2000 // Dispose objects before losing scope
    {
    }

    public MockPipelineMessage(PipelineRequest request) : base(request)
    {
        this.NetworkTimeout ??= Timeout.InfiniteTimeSpan;
    }

    public void SetResponse(PipelineResponse response)
        => this.Response = response;
}

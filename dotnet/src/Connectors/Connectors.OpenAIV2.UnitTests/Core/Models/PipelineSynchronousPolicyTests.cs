// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel.Primitives;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Core.Models;
public class PipelineSynchronousPolicyTests
{
    [Fact]
    public async Task ItProcessAsyncWhenSpecializationHasReceivedResponseOverrideShouldCallIt()
    {
        // Arrange
        var first = new MyHttpPipelinePolicyWithoutOverride();
        var last = new MyHttpPipelinePolicyWithOverride();

        IReadOnlyList<PipelinePolicy> policies = [first, last];

        // Act
        await policies[0].ProcessAsync(ClientPipeline.Create().CreateMessage(), policies, 0);

        // Assert
        Assert.True(first.CalledProcess);
        Assert.True(last.CalledProcess);
        Assert.True(last.CalledOnReceivedResponse);
    }

    private class MyHttpPipelinePolicyWithoutOverride : PipelineSynchronousPolicy
    {
        public bool CalledProcess { get; private set; }

        public override void Process(PipelineMessage message, IReadOnlyList<PipelinePolicy> pipeline, int currentIndex)
        {
            this.CalledProcess = true;
            base.Process(message, pipeline, currentIndex);
        }

        public override ValueTask ProcessAsync(PipelineMessage message, IReadOnlyList<PipelinePolicy> pipeline, int currentIndex)
        {
            this.CalledProcess = true;
            return base.ProcessAsync(message, pipeline, currentIndex);
        }
    }

    private sealed class MyHttpPipelinePolicyWithOverride : MyHttpPipelinePolicyWithoutOverride
    {
        public bool CalledOnReceivedResponse { get; private set; }

        public override void OnReceivedResponse(PipelineMessage message)
        {
            this.CalledOnReceivedResponse = true;
        }
    }
}

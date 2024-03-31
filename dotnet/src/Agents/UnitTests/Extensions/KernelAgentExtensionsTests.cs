// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel;
using System.Collections.Generic;
using System.Threading.Tasks;
using System.Threading;
using System;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Extensions;

public class KernelAgentExtensionsTests
{
    [Fact]
    public async Task TestKernelAgentExtensionsFormatInstructionsAsync()
    {
        TestAgent agent = new(Kernel.CreateBuilder().Build(), "test");

        var instructions = await agent.FormatInstructionsAsync();

        Assert.Equal("test", instructions);
    }

    private sealed class TestAgent(Kernel kernel, string? instructions = null)
        : KernelAgent(kernel, instructions)
    {
        public override string? Description { get; } = null;

        public override string Id => this.Instructions ?? Guid.NewGuid().ToString();

        public override string? Name { get; } = null;

        protected internal override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
        {
            throw new NotImplementedException();
        }

        protected internal override IEnumerable<string> GetChannelKeys()
        {
            throw new NotImplementedException();
        }
    }
}

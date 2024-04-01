// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Extensions;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Extensions;

/// <summary>
/// Unit testing of <see cref="KernelAgentExtensions"/>.
/// </summary>
public class KernelAgentExtensionsTests
{
    /// <summary>
    /// Verify behavior of <see cref="KernelAgentExtensions.FormatInstructionsAsync"/> extension.
    /// </summary>
    [Fact]
    public async Task VerifyKernelAgentExtensionsFormatInstructionsAsync()
    {
        TestAgent agent = new(Kernel.CreateBuilder().Build(), "test");

        var instructions = await agent.FormatInstructionsAsync(agent.Instructions);

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

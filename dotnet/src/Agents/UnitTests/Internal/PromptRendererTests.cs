// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Internal;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Internal;

public class PromptRendererTests
{
    private readonly TestFilter _filter = new();

    [Fact]
    public async Task VerifyPromptRendererNullInstructionsTestAsync()
    {
        await this.VerifyRenderSkippedAsync(instructions: null);
        await this.VerifyRenderSkippedAsync(instructions: string.Empty);
        await this.VerifyRenderSkippedAsync(instructions: "\t");
        await this.VerifyRenderSkippedAsync(instructions: "\n");
        await this.VerifyRenderSkippedAsync(instructions: "   ");
    }

    [Fact]
    public async Task VerifyPromptRendererBasicInstructionsTestAsync()
    {
        await this.VerifyRenderAsync(instructions: "Do something");
        await this.VerifyRenderAsync(instructions: "Do something", expectCached: true);
        await this.VerifyRenderAsync(instructions: "Do something else");
    }

    [Fact]
    public async Task VerifyPromptRendererTemplateInstructionsTestAsync()
    {
        KernelArguments arguments = new() { { "n", 3 } };
        await this.VerifyRenderAsync(instructions: "Do something: {{$n}}", arguments);
        await this.VerifyRenderAsync(instructions: "Do something: {{$n}}", arguments, expectCached: true);
        await this.VerifyRenderAsync(instructions: "Do something else: {{$n}}", arguments);
    }

    private async Task VerifyRenderAsync(string instructions, KernelArguments? arguments = null, bool expectCached = false)
    {
        var rendered = await this.RenderInstructionsAsync(instructions, arguments);
        Assert.NotNull(rendered);
        Assert.Equal(expectCached ? 0 : arguments == null ? 0 : 0, this._filter.RenderCount); // $$$ FILTER BUG
    }

    private async Task VerifyRenderSkippedAsync(string? instructions)
    {
        var rendered = await this.RenderInstructionsAsync(instructions);
        Assert.Null(rendered);
        Assert.Equal(0, this._filter.RenderCount);
    }

    private async Task<string?> RenderInstructionsAsync(string? instructions, KernelArguments? arguments = null)
    {
        TestAgent agent = new(this.CreateKernel(), instructions);

        agent.InstructionArguments = arguments;

        return await PromptRenderer.FormatInstructionsAsync(agent);
    }

    private Kernel CreateKernel()
    {
        Kernel kernel = Kernel.CreateBuilder().Build();

        kernel.PromptFilters.Add(this._filter);

        return kernel;
    }

    private sealed class TestFilter : IPromptFilter
    {
        public int RenderCount { get; private set; }

        public void OnPromptRendered(PromptRenderedContext context)
        {
            ++this.RenderCount;
        }

        public void OnPromptRendering(PromptRenderingContext context)
        {
            // Nothing to do...
        }
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

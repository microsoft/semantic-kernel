// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Agents.Orchestration;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrates how to build a custom <see cref="AgentOrchestration{TInput, TSource, TResult, TOutput}"/>.
/// </summary>
public class Step05_Custom(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Fact]
    public Task UseCustomPatternAsync() // %%% SAMPLE - CUSTOM
    {
        return Task.CompletedTask;
    }
}

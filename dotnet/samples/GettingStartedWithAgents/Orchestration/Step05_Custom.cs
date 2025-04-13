// Copyright (c) Microsoft. All rights reserved.

namespace GettingStarted.Orchestration;

/// <summary>
/// %%% COMMENT
/// </summary>
public class Step05_Custom(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Fact]
    public Task UseCustomPatternAsync()
    {
        return Task.CompletedTask;
    }
}

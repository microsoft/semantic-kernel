// Copyright (c) Microsoft. All rights reserved.

//#define DISABLEHOST // Comment line to enable
using System.Threading.Tasks;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Experimental.Assistants.UnitTests;

/// <summary>
/// $$$
/// </summary>
public sealed class AssistantHarness
{
#if DISABLEHOST
    private const string SkipReason = "Harness only for local/dev environment";
#else
    private const string SkipReason = null;
#endif

    private readonly ITestOutputHelper _output;

    public AssistantHarness(ITestOutputHelper output)
    {
        this._output = output;
    }

    [Fact(Skip = SkipReason)]
    public async Task CreateAssistantAsync()
    {
    }

    [Fact(Skip = SkipReason)]
    public async Task GetAssistantAsync()
    {
    }
}

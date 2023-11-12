// Copyright (c) Microsoft. All rights reserved.

//#define DISABLEHOST // Comment line to enable
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Experimental.Assistants.UnitTests;

/// <summary>
/// Dev harness for manipulating runs.
/// </summary>
public sealed class RunHarness
{
#if DISABLEHOST
    private const string SkipReason = "Harness only for local/dev environment";
#else
    private const string SkipReason = null;
#endif

    private readonly ITestOutputHelper _output;

    /// <summary>
    /// Test contructor.
    /// </summary>
    public RunHarness(ITestOutputHelper output)
    {
        this._output = output;
    }

    [Fact(Skip = SkipReason)]
    public async Task CreateRunAsync()
    {
        using var httpClient = new HttpClient();
        var context = OpenAIRestContext.CreateFromConfig(httpClient);

        var run = await ChatRun.CreateAsync(context, "thread_AQf7ra5DJIsUnLegytkski90", "asst_agi0P2OKJEBVrHN5Rcu0r2fy").ConfigureAwait(true);

        this._output.WriteLine($"# {run.Id}");

        var result = await run.GetResultAsync().ConfigureAwait(true);

        this._output.WriteLine($"$ {result}");
    }
}

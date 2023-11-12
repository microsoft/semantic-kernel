// Copyright (c) Microsoft. All rights reserved.

//#define DISABLEHOST // Comment line to enable
using System;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Experimental.Assistants;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Experimental.Assistants.UnitTests;

/// <summary>
/// $$$
/// </summary>
public sealed class ThreadHarness
{
#if DISABLEHOST
    private const string SkipReason = "Harness only for local/dev environment";
#else
    private const string SkipReason = null;
#endif

    private readonly ITestOutputHelper _output;

    public ThreadHarness(ITestOutputHelper output)
    {
        this._output = output;
    }

    [Fact(Skip = SkipReason)]
    public async Task CreateThreadAsync()
    {
        using var httpClient = new HttpClient();
        var context = OpenAIRestContext.CreateFromConfig(httpClient);

        var thread = await ChatThread.CreateAsync(context).ConfigureAwait(true);

        this._output.WriteLine($"# {thread.Id}");
    }

    [Fact(Skip = SkipReason)]
    public async Task GetThreadAsync()
    {
        using var httpClient = new HttpClient();
        var context = OpenAIRestContext.CreateFromConfig(httpClient);

        var thread = new ChatThread("thread_AQf7ra5DJIsUnLegytkski90", context);
    }

    [Fact(Skip = SkipReason)]
    public async Task AddThreadMessageAsync()
    {
        using var httpClient = new HttpClient();
        var context = OpenAIRestContext.CreateFromConfig(httpClient);

        var thread = new ChatThread("thread_AQf7ra5DJIsUnLegytkski90", context);
        await thread.AddUserMessageAsync("I'm so confused!").ConfigureAwait(true); ;
    }
}

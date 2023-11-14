// Copyright (c) Microsoft. All rights reserved.

//#define DISABLEHOST // Comment line to enable
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Experimental.Assistants.UnitTests;

/// <summary>
/// Dev harness for manipulating threads.
/// </summary>
public sealed class ThreadHarness
{
#if DISABLEHOST
    private const string SkipReason = "Harness only for local/dev environment";
#else
    private const string SkipReason = null;
#endif

    private readonly ITestOutputHelper _output;

    /// <summary>
    /// Test constructor.
    /// </summary>
    public ThreadHarness(ITestOutputHelper output)
    {
        this._output = output;
    }

    /// <summary>
    /// Verify creation and retrieval of thread.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task VerifyThreadLifecycleAsync()
    {
        using var httpClient = new HttpClient();
        var context = OpenAIRestContext.CreateFromConfig(httpClient);

        var thread = await context.CreateThreadAsync().ConfigureAwait(true);

        Assert.NotNull(thread.Id);

        this._output.WriteLine($"# {thread.Id}");

        var message = await thread.AddUserMessageAsync("I'm so confused!").ConfigureAwait(true);
        Assert.NotNull(message);

        this._output.WriteLine($"# {message.Id}");

        var copy = await context.GetThreadAsync(thread.Id).ConfigureAwait(true);
    }
}

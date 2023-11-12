// Copyright (c) Microsoft. All rights reserved.

//#define DISABLEHOST // Comment line to enable
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;
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
    /// Test contructor.
    /// </summary>
    public ThreadHarness(ITestOutputHelper output)
    {
        this._output = output;
    }

    /// <summary>
    /// Create a new thread.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task CreateThreadAsync()
    {
        using var httpClient = new HttpClient();
        var context = OpenAIRestContext.CreateFromConfig(httpClient);

        var thread = await ChatThread.CreateAsync(context).ConfigureAwait(true);

        this._output.WriteLine($"# {thread.Id}");
    }

    /// <summary>
    /// Retrieve an thread.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task GetThreadAsync()
    {
        using var httpClient = new HttpClient();
        var context = OpenAIRestContext.CreateFromConfig(httpClient);

        var thread = await ChatThread.GetAsync(context, "thread_AQf7ra5DJIsUnLegytkski90").ConfigureAwait(true);
    }

    /// <summary>
    /// Add a message to existing thread.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task AddThreadMessageAsync()
    {
        using var httpClient = new HttpClient();
        var context = OpenAIRestContext.CreateFromConfig(httpClient);

        var thread = await ChatThread.GetAsync(context, "thread_AQf7ra5DJIsUnLegytkski90").ConfigureAwait(true);
        await thread.AddUserMessageAsync("I'm so confused!").ConfigureAwait(true);
    }

    /// <summary>
    /// Retrieve messages from existing thread.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task GetThreadMessagesAsync()
    {
        using var httpClient = new HttpClient();
        var context = OpenAIRestContext.CreateFromConfig(httpClient);

        var thread = await ChatThread.GetAsync(context, "thread_AQf7ra5DJIsUnLegytkski90").ConfigureAwait(true);
        var messages = await thread.GetMessagesAsync().ConfigureAwait(true);
        foreach (var message in messages)
        {
            this._output.WriteLine($"{message.Role}: {message.Content} [{message.AssistantId}]");
        }
    }
}

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
    public async Task VerifyThreadLifecycleAsync()
    {
        using var httpClient = new HttpClient();
        var context = OpenAIRestContext.CreateFromConfig(httpClient);

        var thread = await context.CreateThreadAsync().ConfigureAwait(true);

        Assert.NotNull(thread.Id);
        Assert.NotNull(thread.Messages);
        Assert.Empty(thread.Messages);

        this._output.WriteLine($"# {thread.Id}");

        var message = await thread.AddUserMessageAsync("I'm so confused!").ConfigureAwait(true);
        Assert.NotNull(message);
        Assert.NotNull(message.Id);
        Assert.Single(thread.Messages);

        this._output.WriteLine($"# {message.Id}");
        this.DumpMessages(thread);

        var copy = await context.GetThreadAsync(thread.Id).ConfigureAwait(true);
        this.DumpMessages(copy);
    }

    private void DumpMessages(IChatThread thread)
    {
        foreach (var message in thread.Messages)
        {
            if (string.IsNullOrWhiteSpace(message.AssistantId))
            {
                this._output.WriteLine($"{message.Role}: {message.Content}");
            }
            else
            {
                this._output.WriteLine($"{message.Role}: {message.Content} [{message.AssistantId}]");
            }
        }
    }
}

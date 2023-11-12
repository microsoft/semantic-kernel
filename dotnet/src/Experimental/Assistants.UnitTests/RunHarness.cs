// Copyright (c) Microsoft. All rights reserved.

//#define DISABLEHOST // Comment line to enable
using System.Linq;
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

    /// <summary>
    /// Verify creation of run.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task VerifyRunLifecycleAsync()
    {
        using var httpClient = new HttpClient();
        var context = OpenAIRestContext.CreateFromConfig(httpClient);

        var assistant =
            await context.CreateAssistantAsync(
                model: "gpt-3.5-turbo-1106",
                instructions: "say something funny",
                name: "Fred",
                description: "funny assistant").ConfigureAwait(true);

        var thread = await context.CreateThreadAsync().ConfigureAwait(true);
        var messageUser = await thread.AddUserMessageAsync("I was on my way to the store this morning and...").ConfigureAwait(true);

        var messages = await thread.InvokeAsync(assistant.Id).ConfigureAwait(true);
        var message = messages.First(); // $$$ HAXX
        this._output.WriteLine($"# {message.Id}");
        this._output.WriteLine($"# {message.Content}");
        this._output.WriteLine($"# {message.Role}");
        this._output.WriteLine($"# {message.AssistantId}");

        //var run = await ChatRun.CreateAsync(context, "thread_AQf7ra5DJIsUnLegytkski90", "asst_agi0P2OKJEBVrHN5Rcu0r2fy").ConfigureAwait(true);
        //this._output.WriteLine($"# {run.Id}");
        //var result = await run.GetResultAsync().ConfigureAwait(true);
        //this._output.WriteLine($"$ {result}");
    }
}

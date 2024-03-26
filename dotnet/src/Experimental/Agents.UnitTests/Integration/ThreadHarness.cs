// Copyright (c) Microsoft. All rights reserved.

#define DISABLEHOST // Comment line to enable
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Experimental.Agents;
using Microsoft.SemanticKernel.Experimental.Agents.Internal;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Experimental.Agents.UnitTests.Integration;

/// <summary>
/// Dev harness for manipulating threads.
/// </summary>
/// <remarks>
/// Comment out DISABLEHOST definition to enable tests.
/// Not enabled by default.
/// </remarks>
[Trait("Category", "Integration Tests")]
[Trait("Feature", "Agent")]
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
        var agent =
            await new AgentBuilder()
                .WithOpenAIChatCompletion(TestConfig.SupportedGpt35TurboModel, TestConfig.OpenAIApiKey)
                .WithName("DeleteMe")
                .BuildAsync()
                .ConfigureAwait(true);

        var thread = await agent.NewThreadAsync().ConfigureAwait(true);

        Assert.NotNull(thread.Id);

        this._output.WriteLine($"# {thread.Id}");

        var message = await thread.AddUserMessageAsync("I'm so confused!").ConfigureAwait(true);
        Assert.NotNull(message);

        this._output.WriteLine($"# {message.Id}");

        var context = new OpenAIRestContext(AgentBuilder.OpenAIBaseUrl, TestConfig.OpenAIApiKey);
        var copy = await context.GetThreadModelAsync(thread.Id).ConfigureAwait(true);

        await context.DeleteThreadModelAsync(thread.Id).ConfigureAwait(true);

        await Assert.ThrowsAsync<HttpOperationException>(() => context.GetThreadModelAsync(thread.Id)).ConfigureAwait(true);
    }

    /// <summary>
    /// Verify retrieval of thread messages
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task GetThreadAsync()
    {
        var threadId = "<your thread-id>";

        var context = new OpenAIRestContext(AgentBuilder.OpenAIBaseUrl, TestConfig.OpenAIApiKey);
        var thread = await ChatThread.GetAsync(context, threadId);

        int index = 0;
        string? messageId = null;
        while (messageId != null || index == 0)
        {
            var messages = await thread.GetMessagesAsync(count: 100, lastMessageId: messageId).ConfigureAwait(true);
            foreach (var message in messages)
            {
                ++index;
                this._output.WriteLine($"#{index:000} [{message.Id}] {message.Role} [{message.AgentId ?? "n/a"}]");

                this._output.WriteLine(message.Content);
            }

            messageId = messages.Count > 0 ? messages[messages.Count - 1].Id : null;
        }
    }
}

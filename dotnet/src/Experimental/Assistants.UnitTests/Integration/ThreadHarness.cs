// Copyright (c) Microsoft. All rights reserved.

#define DISABLEHOST // Comment line to enable
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Experimental.Assistants;
using Microsoft.SemanticKernel.Experimental.Assistants.Extensions;
using Microsoft.SemanticKernel.Experimental.Assistants.Internal;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Experimental.Assistants.UnitTests.Integration;

/// <summary>
/// Dev harness for manipulating threads.
/// </summary>
/// <remarks>
/// Comment out DISABLEHOST definition to enable tests.
/// Not enabled by default.
/// </remarks>
[Trait("Category", "Integration Tests")]
[Trait("Feature", "Assistant")]
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
        var assistant =
            await new AssistantBuilder()
                .WithOpenAIChatCompletionService(TestConfig.SupportedGpt35TurboModel, TestConfig.OpenAIApiKey)
                .WithName("DeleteMe")
                .BuildAsync()
                .ConfigureAwait(true);

        var thread = await assistant.NewThreadAsync().ConfigureAwait(true);

        Assert.NotNull(thread.Id);

        this._output.WriteLine($"# {thread.Id}");

        var message = await thread.AddUserMessageAsync("I'm so confused!").ConfigureAwait(true);
        Assert.NotNull(message);

        this._output.WriteLine($"# {message.Id}");

        var context = new OpenAIRestContext(TestConfig.OpenAIApiKey);
        var copy = await context.GetThreadModelAsync(thread.Id).ConfigureAwait(true);

        await context.DeleteThreadModelAsync(thread.Id).ConfigureAwait(true);

        await Assert.ThrowsAsync<KernelException>(() => context.GetThreadModelAsync(thread.Id)).ConfigureAwait(true);
    }
}

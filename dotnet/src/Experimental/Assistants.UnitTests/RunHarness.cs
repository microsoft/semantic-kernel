// Copyright (c) Microsoft. All rights reserved.

//#define DISABLEHOST // Comment line to enable
using System.Collections.Generic;
using System.ComponentModel;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
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
    /// Test constructor.
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

        await this.ChatAsync(
            thread,
            assistant,
            "I was on my way to the store this morning and...",
            "That was great!  Tell me another.").ConfigureAwait(true);

        var copy = await context.GetThreadAsync(thread.Id).ConfigureAwait(true);
    }

    /// <summary>
    /// Verify creation of run.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task VerifyRunFromDefinitionAsync()
    {
        using var httpClient = new HttpClient();
        var context = OpenAIRestContext.CreateFromConfig(httpClient);

        var assistant =
            await context.CreateAssistantAsync(
                model: "gpt-3.5-turbo-1106",
                configurationPath: "PoetAssistant.yaml").ConfigureAwait(true);

        var thread = await context.CreateThreadAsync().ConfigureAwait(true);

        await this.ChatAsync(
            thread,
            assistant,
            "Eggs are yummy and beautiful geometric gems.",
            "It rains a lot in Seattle.").ConfigureAwait(true);

        var copy = await context.GetThreadAsync(thread.Id).ConfigureAwait(true);
    }

    /// <summary>
    /// Verify creation of run.
    /// </summary>
    [Fact(Skip = SkipReason)]
    public async Task VerifyFunctionLifecycleAsync()
    {
        using var httpClient = new HttpClient();
        var context = OpenAIRestContext.CreateFromConfig(httpClient);

        var kernel = new KernelBuilder().Build();

        var gamePlugin = kernel.ImportFunctions(new GuessingGame(), nameof(GuessingGame));

        var assistant =
            await context.CreateAssistantAsync(
                model: "gpt-3.5-turbo-1106",
                configurationPath: "GameAssistant.yaml",
                functions: gamePlugin.Values).ConfigureAwait(true);

        var thread = await context.CreateThreadAsync().ConfigureAwait(true);
        await this.ChatAsync(
            thread,
            assistant,
            "What is the question for the guessing game?",
            "Is it 'RED'?",
            "What is the answer?").ConfigureAwait(true);

        var copy = await context.GetThreadAsync(thread.Id).ConfigureAwait(true);
    }

    private async Task ChatAsync(IChatThread thread, IAssistant assistant, params string[] messages)
    {
        foreach (var message in messages)
        {
            var messageUser = await thread.AddUserMessageAsync(message).ConfigureAwait(true);
            this.LogMessage(messageUser);

            var assistantMessages = await thread.InvokeAsync(assistant).ConfigureAwait(true);
            this.LogMessages(assistantMessages);
        }
    }

    private void LogMessages(IEnumerable<IChatMessage> messages)
    {
        foreach (var message in messages)
        {
            this.LogMessage(message);
        }
    }

    private void LogMessage(IChatMessage message)
    {
        this._output.WriteLine($"# {message.Id}");
        this._output.WriteLine($"# {message.Content}");
        this._output.WriteLine($"# {message.Role}");
        this._output.WriteLine($"# {message.AssistantId}");
    }

    private sealed class GuessingGame
    {
        /// <summary>
        /// Get the question
        /// </summary>
        [SKFunction, Description("Get the guessing game question")]
        public string GetQuestion() => "What color am I thinking of?";

        /// <summary>
        /// Get the answer
        /// </summary>
        [SKFunction, Description("Get the answer to the guessing game question.")]
        public string GetAnswer() => "Blue";
    }
}

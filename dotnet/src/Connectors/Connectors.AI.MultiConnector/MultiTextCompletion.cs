// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Channels;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.MultiConnector.Analysis;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

/// <summary>
/// Represents a text completion comprising several child completion connectors and capable of routing completion calls to specific connectors.
/// Offers analysis capabilities where a primary completion connector is tasked with vetting secondary connectors.
/// </summary>
public class MultiTextCompletion : ITextCompletion
{
    private readonly ILogger? _logger;
    private readonly IReadOnlyList<NamedTextCompletion> _textCompletions;
    private readonly MultiTextCompletionSettings _settings;
    private readonly Channel<ConnectorTest> _dataCollectionChannel;

    /// <summary>
    /// Initializes a new instance of the MultiTextCompletion class.
    /// </summary>
    /// <param name="settings">An instance of the <see cref="MultiTextCompletionSettings"/> to configure the multi Text completion.</param>
    /// <param name="mainTextCompletion">The primary text completion to used by default for completion calls and vetting other completion providers.</param>
    /// <param name="analysisTaskCancellationToken">The cancellation token to use for the completion manager.</param>
    /// <param name="logger">An optional logger for instrumentation.</param>
    /// <param name="otherCompletions">The secondary text completions that need vetting to be used for completion calls.</param>
    public MultiTextCompletion(MultiTextCompletionSettings settings,
        NamedTextCompletion mainTextCompletion,
        CancellationToken? analysisTaskCancellationToken,
        ILogger? logger = null,
        params NamedTextCompletion[]? otherCompletions)
    {
        this._settings = settings;
        this._logger = logger;
        this._textCompletions = new[] { mainTextCompletion }.Concat(otherCompletions ?? Array.Empty<NamedTextCompletion>()).ToArray();
        this._dataCollectionChannel = Channel.CreateUnbounded<ConnectorTest>();

        this.StartManagementTask(analysisTaskCancellationToken ?? CancellationToken.None);
    }

    /// <inheritdoc />
    public async Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(string text, CompleteRequestSettings requestSettings, CancellationToken cancellationToken = default)
    {
        this._logger?.LogTrace("## Starting MultiTextCompletion.GetCompletionsAsync");
        var completionJob = new CompletionJob(text, requestSettings);
        var session = this.GetPromptAndConnectorSettings(completionJob);
        this._logger?.LogTrace("### Calling chosen completion with adjusted prompt and settings");
        var completions = await session.NamedTextCompletion.TextCompletion.GetCompletionsAsync(session.CallJob.Prompt, session.CallJob.RequestSettings, cancellationToken).ConfigureAwait(false);

        var resultLazy = new AsyncLazy<string>(() =>
        {
            var toReturn = completions[0].GetCompletionAsync(cancellationToken);
            session.Stopwatch.Stop();
            return toReturn;
        }, cancellationToken);

        session.ResultProducer = resultLazy;

        await this.ProcessTextCompletionResultsAsync(session, cancellationToken).ConfigureAwait(false);

        this._logger?.LogTrace("## Ending MultiTextCompletion.GetCompletionsAsync");
        return completions;
    }

    /// <inheritdoc />
    public IAsyncEnumerable<ITextStreamingResult> GetStreamingCompletionsAsync(string text, CompleteRequestSettings requestSettings, CancellationToken cancellationToken = default)
    {
        this._logger?.LogTrace("## Starting MultiTextCompletion.GetStreamingCompletionsAsync");
        var completionJob = new CompletionJob(text, requestSettings);
        var session = this.GetPromptAndConnectorSettings(completionJob);
        this._logger?.LogTrace("### Calling chosen completion with adjusted prompt and settings");
        var result = session.NamedTextCompletion.TextCompletion.GetStreamingCompletionsAsync(session.CallJob.Prompt, session.CallJob.RequestSettings, cancellationToken);

        var resultLazy = new AsyncLazy<string>(async () =>
        {
            var sb = new StringBuilder();
            await foreach (var completionResult in result.WithCancellation(cancellationToken))
            {
                await foreach (var word in completionResult.GetCompletionStreamingAsync(cancellationToken).ConfigureAwait(false))
                {
                    sb.Append(word);
                }

                break;
            }

            session.Stopwatch.Stop();
            return sb.ToString();
        }, cancellationToken);

        session.ResultProducer = resultLazy;

        this.ProcessTextCompletionResultsAsync(session, cancellationToken).ConfigureAwait(false);

        this._logger?.LogTrace("## Ending MultiTextCompletion.GetStreamingCompletionsAsync");

        return result;
    }

    /// <summary>
    /// This method is responsible for loading the appropriate settings in order to initiate the session state
    /// </summary>
    private MultiCompletionSession GetPromptAndConnectorSettings(CompletionJob completionJob)
    {
        var promptSettings = this._settings.GetPromptSettings(completionJob, out var isNewPrompt);
        this._logger?.LogTrace("### Retrieved prompt type and settings for connector, prompt signature:{0}", promptSettings.PromptType.Signature.PromptStart);
        var textCompletionAndSettings = promptSettings.SelectAppropriateTextCompletion(completionJob, this._textCompletions, this._settings.ConnectorComparer);
        this._logger?.LogTrace("### Selected connector for prompt type: {0}", textCompletionAndSettings.namedTextCompletion.Name);

        var session = new MultiCompletionSession(completionJob,
            promptSettings,
            isNewPrompt,
            textCompletionAndSettings.namedTextCompletion,
            this._textCompletions,
            textCompletionAndSettings.promptConnectorSettings,
            this._settings,
            this._logger);

        session.AdjustPromptAndRequestSettings();

        return session;
    }

    /// <summary>
    /// This method ends the multi-completion session and collects the results for analysis if needed
    /// </summary>
    private async Task ProcessTextCompletionResultsAsync(MultiCompletionSession session, CancellationToken cancellationToken)
    {
        var costDebited = await this.ApplyCreditorCostsAsync(session.CallJob.Prompt, session.ResultProducer, session.NamedTextCompletion).ConfigureAwait(false);

        if (this._settings.EnablePromptSampling && session.PromptSettings.IsSampleNeeded(session))
        {
            session.PromptSettings.AddSessionPrompt(session.InputJob.Prompt);
            await this.CollectResultForTestAsync(session, costDebited, cancellationToken).ConfigureAwait(false);
        }

        if (this._settings.LogCallResult)
        {
            var connectorName = session.NamedTextCompletion.Name;
            var duration = session.Stopwatch.Elapsed;
            var callPromptText = session.CallJob.Prompt;
            var result = await session.ResultProducer.Value.ConfigureAwait(false);
            this._logger?.LogInformation("\n\nMULTI-COMPLETION returned for connector: {0}: duration:{1} \nADJUSTED PROMPT:\n{2}\n\nRESULT:\n{3}\n\n",
                connectorName,
                duration,
                this._settings.GeneratePromptLog(callPromptText),
                this._settings.GeneratePromptLog(result));
        }
    }

    /// <summary>
    /// This method applies the cost of the text completion (input + result) to the creditor if one is configured
    /// </summary>
    private async Task<decimal> ApplyCreditorCostsAsync(string text, AsyncLazy<string> resultLazy, NamedTextCompletion textCompletion)
    {
        decimal cost = 0;
        if (this._settings.Creditor != null)
        {
            var result = await resultLazy.Value.ConfigureAwait(false);
            cost = textCompletion.GetCost(text, result);
            this._settings.Creditor.Credit(cost);
        }

        return cost;
    }

    /// <summary>
    /// Asynchronously collects results from a prompt call to evaluate connectors against the same prompt.
    /// </summary>
    private async Task CollectResultForTestAsync(MultiCompletionSession session, decimal textCompletionCost, CancellationToken cancellationToken)
    {
        var result = await session.ResultProducer.Value.ConfigureAwait(false);

        var duration = session.Stopwatch.Elapsed;

        // For the management task
        ConnectorTest connectorTest = ConnectorTest.Create(session.InputJob, session.NamedTextCompletion, result, duration, textCompletionCost);
        this.AppendConnectorTest(connectorTest);
    }

    /// <summary>
    /// Starts a management task charged with collecting and analyzing prompt connector usage.
    /// </summary>
    private void StartManagementTask(CancellationToken cancellationToken)
    {
        Task.Factory.StartNew(
            async () =>
            {
                while (!cancellationToken.IsCancellationRequested)
                {
                    await this.CollectSamplesAsync(cancellationToken).ConfigureAwait(false);
                }
            },
            cancellationToken,
            TaskCreationOptions.LongRunning,
            TaskScheduler.Default);
    }

    /// <summary>
    /// Asynchronously receives new ConnectorTest from completion calls, evaluate available connectors against tests and perform analysis to vet connectors.
    /// </summary>
    private async Task CollectSamplesAsync(CancellationToken cancellationToken)
    {
        try
        {
            while (await this._dataCollectionChannel.Reader.WaitToReadAsync(cancellationToken).ConfigureAwait(false))
            {
                var testSeries = new List<ConnectorTest>();

                while (this._dataCollectionChannel.Reader.TryRead(out var newSample))
                {
                    if (!cancellationToken.IsCancellationRequested)
                    {
                        var now = DateTime.Now;
                        var delay = newSample.Timestamp + this._settings.SampleCollectionDelay - now;

                        if (delay > TimeSpan.FromMilliseconds(1))
                        {
                            this._logger?.LogTrace(message: "CollectSamplesAsync adding collection delay {0}", delay);
                            await Task.Delay(delay, cancellationToken).ConfigureAwait(false);
                        }

                        testSeries.Add(newSample);
                    }
                }

                this._logger?.LogTrace(message: "## CollectSamplesAsync collected a new ConnectorTest series to analyze", testSeries);

                var analysisJob = new AnalysisJob(this._settings, this._textCompletions, this._logger, cancellationToken);
                // Save the tests
                var needTest = this._settings.AnalysisSettings.SaveSamplesNeedRunningTest(testSeries, analysisJob);

                if (needTest)
                {
                    // Once you have a batch ready, write it to the channel
                    await this._settings.AnalysisSettings.AddAnalysisJobAsync(analysisJob).ConfigureAwait(false);
                }
            }
        }
        catch (OperationCanceledException exception)
        {
            this._logger?.LogTrace("CollectSamplesAsync task was cancelled with exception {0}", exception, exception.ToString());
        }
        catch (Exception exception)
        {
            var message = "CollectSamplesAsync task failed";
            this._logger?.LogError("{0} with exception {1}", exception, message, exception.ToString());
            throw new SKException(message, exception);
        }
    }

    /// <summary>
    /// Appends a connector test to the test channel listened to in the Optimization long running task.
    /// </summary>
    private void AppendConnectorTest(ConnectorTest connectorTest)
    {
        if (this._settings.LogTestCollection)
        {
            this._logger?.LogDebug("Collecting new original sample to test with duration {0},\nORIGINAL_PROMPT:\n{1}\nORIGINAL_RESULT:\n{2}", connectorTest.Duration,
                this._settings.GeneratePromptLog(connectorTest.Prompt),
                this._settings.GeneratePromptLog(connectorTest.Result));
        }

        this._dataCollectionChannel.Writer.TryWrite(connectorTest);
    }
}

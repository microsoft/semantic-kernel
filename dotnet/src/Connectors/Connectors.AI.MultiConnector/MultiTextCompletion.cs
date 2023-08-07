// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Channels;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;

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
    private readonly Channel<ConnectorTest> _connectorTestChannel;

    /// <summary>
    /// An optional creditor that will compute compound costs from the connectors settings and usage.
    /// </summary>
    public CallRequestCostCreditor? Creditor { get; set; }

    /// <summary>
    /// Initializes a new instance of the MultiTextCompletion class.
    /// </summary>
    /// <param name="settings">An instance of the <see cref="MultiTextCompletionSettings"/> to configure the multi Text completion.</param>
    /// <param name="mainTextCompletion">The primary text completion to used by default for completion calls and vetting other completion providers.</param>
    /// <param name="analysisTaskCancellationToken">The cancellation token to use for the completion manager.</param>
    /// <param name="creditor">an optional cost counter that will compute the compound costs from settings and connector usage</param>
    /// <param name="logger">An optional logger for instrumentation.</param>
    /// <param name="otherCompletions">The secondary text completions that need vetting to be used for completion calls.</param>
    public MultiTextCompletion(MultiTextCompletionSettings settings, NamedTextCompletion mainTextCompletion, CancellationToken? analysisTaskCancellationToken, CallRequestCostCreditor? creditor = null, ILogger? logger = null, params NamedTextCompletion[] otherCompletions)
    {
        this._settings = settings;
        this._logger = logger;
        this.Creditor = creditor;
        this._textCompletions = new[] { mainTextCompletion }.Concat(otherCompletions).ToArray();
        this._connectorTestChannel = Channel.CreateUnbounded<ConnectorTest>();
        this.StartManagementTask(analysisTaskCancellationToken ?? CancellationToken.None);
    }

    /// <inheritdoc />
    private sealed class AsyncLazy<T> : Lazy<Task<T>>
    {
        public AsyncLazy(T value)
            : base(() => Task.FromResult(value))
        {
        }

        public AsyncLazy(Func<T> valueFactory, CancellationToken cancellationToken)
            : base(() => Task.Factory.StartNew<T>(valueFactory, cancellationToken, TaskCreationOptions.None, TaskScheduler.Current))
        {
        }

        public AsyncLazy(Func<Task<T>> taskFactory, CancellationToken cancellationToken)
            : base(() => Task.Factory.StartNew(taskFactory, cancellationToken, TaskCreationOptions.None, TaskScheduler.Current).Unwrap())
        {
        }
    }

    public async Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(string text, CompleteRequestSettings requestSettings, CancellationToken cancellationToken = default)
    {
        var promptSettings = this._settings.GetPromptSettings(text, requestSettings);
        var textCompletion = promptSettings.SelectAppropriateTextCompletion(this._textCompletions, this._settings.ConnectorComparer);

        var stopWatch = Stopwatch.StartNew();

        var completions = await textCompletion.TextCompletion.GetCompletionsAsync(text, requestSettings, cancellationToken).ConfigureAwait(false);

        var resultLazy = new AsyncLazy<string>(() => completions[0].GetCompletionAsync(cancellationToken), cancellationToken);

        if (this.Creditor != null)
        {
            var result = await resultLazy.Value.ConfigureAwait(false);
            var cost = textCompletion.GetCost(text, result);
            this.Creditor.Credit(cost);
        }

        if (promptSettings.IsTestingNeeded(this._textCompletions))
        {
            promptSettings.IsTesting = true;
            await this.CollectResultForTestAsync(text, requestSettings, completions, stopWatch, textCompletion, resultLazy, cancellationToken).ConfigureAwait(false);
        }

        return completions;
    }

    /// <summary>
    /// Asynchronously collects results from a prompt call to evaluate connectors against the same prompt.
    /// </summary>
    private async Task CollectResultForTestAsync(string text, CompleteRequestSettings requestSettings, IReadOnlyList<ITextResult> completions, Stopwatch stopWatch, NamedTextCompletion textCompletion, AsyncLazy<string> resultLazy, CancellationToken cancellationToken)
    {
        var result = await resultLazy.Value.ConfigureAwait(false);

        stopWatch.Stop();
        var duration = stopWatch.Elapsed;

        // For the management task
        ConnectorTest connectorTest = ConnectorTest.Create(text, requestSettings, textCompletion, result, duration);
        this.AppendConnectorTest(connectorTest);
    }

    /// <inheritdoc />
    public IAsyncEnumerable<ITextStreamingResult> GetStreamingCompletionsAsync(string text, CompleteRequestSettings requestSettings, CancellationToken cancellationToken = default)
    {
        var promptSettings = this._settings.GetPromptSettings(text, requestSettings);
        var textCompletion = promptSettings.SelectAppropriateTextCompletion(this._textCompletions, this._settings.ConnectorComparer);

        var result = textCompletion.TextCompletion.GetStreamingCompletionsAsync(text, requestSettings, cancellationToken);

        _ = this.CollectStreamingTestResultAsync(text, requestSettings, textCompletion, result, cancellationToken);

        return result;
    }

    /// <summary>
    /// Asynchronously collects streaming test results.
    /// </summary>
    private async Task CollectStreamingTestResultAsync(string text, CompleteRequestSettings requestSettings, NamedTextCompletion textCompletion, IAsyncEnumerable<ITextStreamingResult> results, CancellationToken cancellationToken)
    {
        var stopWatch = Stopwatch.StartNew();

        var collectedResult = new StringBuilder();
        // The test result will be collected when it becomes available.
        await foreach (var result in results.WithCancellation(cancellationToken))
        {
            collectedResult.Append(await result.GetCompletionAsync(cancellationToken).ConfigureAwait(false));
        }

        stopWatch.Stop();
        var duration = stopWatch.Elapsed;

        var connectorTest = ConnectorTest.Create(text, requestSettings, textCompletion, collectedResult.ToString(), duration);

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
                    await this.OptimizeCompletionsAsync(cancellationToken).ConfigureAwait(false);
                }
            },
            cancellationToken,
            TaskCreationOptions.LongRunning,
            TaskScheduler.Default);
    }

    /// <summary>
    /// Asynchronously receives new ConnectorTest from completion calls, evaluate available connectors against tests and perform analysis to vet connectors.
    /// </summary>
    private async Task OptimizeCompletionsAsync(CancellationToken cancellationToken)
    {
        try
        {
            while (await this._connectorTestChannel.Reader.WaitToReadAsync(cancellationToken).ConfigureAwait(false))
            {
                while (this._connectorTestChannel.Reader.TryRead(out var connectorTest))
                {
                    if (!cancellationToken.IsCancellationRequested)
                    {
                        await Task.Delay(this._settings.AnalysisSettings.AnalysisDelay, cancellationToken).ConfigureAwait(false);
                        // Evaluate the test
                        await this._settings.AnalysisSettings.EvaluatePromptConnectorsAsync(connectorTest, this._textCompletions, this._settings, this._logger, cancellationToken).ConfigureAwait(false);
                    }
                }

                // Raise the event after optimization is done
                this.OnOptimizationCompleted();
            }
        }
        catch (OperationCanceledException exception)
        {
            this._logger?.LogTrace(message: "OptimizeCompletionsAsync Optimize task was cancelled", exception: exception);
        }
        catch (Exception exception)
        {
            this._logger?.LogError(message: "OptimizeCompletionsAsync Optimize task failed with exception", exception: exception);
            throw;
        }
    }

    // Define the event
    public event EventHandler? OptimizationCompleted;

    // Method to raise the event
    protected virtual void OnOptimizationCompleted()
    {
        this.OptimizationCompleted?.Invoke(this, EventArgs.Empty);
    }

    /// <summary>
    /// Appends a connector test to the test channel listened to in the Optimization long running task.
    /// </summary>
    private void AppendConnectorTest(ConnectorTest connectorTest)
    {
        this._connectorTestChannel.Writer.TryWrite(connectorTest);
    }
}

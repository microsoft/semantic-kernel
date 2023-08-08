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
    public MultiTextCompletion(MultiTextCompletionSettings settings, NamedTextCompletion mainTextCompletion, CancellationToken? analysisTaskCancellationToken, CallRequestCostCreditor? creditor = null, ILogger? logger = null, params NamedTextCompletion[]? otherCompletions)
    {
        this._settings = settings;
        this._logger = logger;
        this.Creditor = creditor;
        this._textCompletions = new[] { mainTextCompletion }.Concat(otherCompletions ?? Array.Empty<NamedTextCompletion>()).ToArray();
        this._connectorTestChannel = Channel.CreateUnbounded<ConnectorTest>();
        this.StartManagementTask(analysisTaskCancellationToken ?? CancellationToken.None);
    }

    /// <inheritdoc />
    public async Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(string text, CompleteRequestSettings requestSettings, CancellationToken cancellationToken = default)
    {
        var promptSettings = this.GetPromptAndConnectorSettings(text, ref requestSettings, out bool isNewPrompt, out NamedTextCompletion textCompletion, out Stopwatch stopWatch);

        var completions = await textCompletion.TextCompletion.GetCompletionsAsync(text, requestSettings, cancellationToken).ConfigureAwait(false);

        var resultLazy = new AsyncLazy<string>(() => completions[0].GetCompletionAsync(cancellationToken), cancellationToken);

        await this.ApplyCreditorCostsAsync(text, resultLazy, textCompletion).ConfigureAwait(false);

        if (textCompletion == this._textCompletions[0] && this._settings.AnalysisSettings.EnableAnalysis && promptSettings.IsTestingNeeded(text, this._textCompletions, isNewPrompt))
        {
            promptSettings.AddSessionPrompt(text);
            await this.CollectResultForTestAsync(text, requestSettings, stopWatch, textCompletion, resultLazy, cancellationToken).ConfigureAwait(false);
        }

        if (this._settings.LogResult)
        {
            this._logger?.LogInformation("MultiTextCompletion.GetCompletionsAsync: {0}\n=>\n {1}", text, resultLazy.Value.ConfigureAwait(false));
        }

        return completions;
    }

    /// <inheritdoc />
    public IAsyncEnumerable<ITextStreamingResult> GetStreamingCompletionsAsync(string text, CompleteRequestSettings requestSettings, CancellationToken cancellationToken = default)
    {
        var promptSettings = this.GetPromptAndConnectorSettings(text, ref requestSettings, out bool isNewPrompt, out NamedTextCompletion textCompletion, out Stopwatch stopWatch);

        var result = textCompletion.TextCompletion.GetStreamingCompletionsAsync(text, requestSettings, cancellationToken);

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

            return sb.ToString();
        }, cancellationToken);

        this.ApplyCreditorCostsAsync(text, resultLazy, textCompletion).ConfigureAwait(false);

        if (textCompletion == this._textCompletions[0] && this._settings.AnalysisSettings.EnableAnalysis && promptSettings.IsTestingNeeded(text, this._textCompletions, isNewPrompt))
        {
            promptSettings.AddSessionPrompt(text);
            this.CollectResultForTestAsync(text, requestSettings, stopWatch, textCompletion, resultLazy, cancellationToken).ConfigureAwait(false);
        }

        if (this._settings.LogResult)
        {
            this._logger?.LogInformation("MultiTextCompletion.GetCompletionsAsync: {0}\n=>\n {1}", text, resultLazy.Value.ConfigureAwait(false));
        }

        return result;
    }

    private PromptMultiConnectorSettings GetPromptAndConnectorSettings(string text, ref CompleteRequestSettings requestSettings, out bool isNewPrompt, out NamedTextCompletion textCompletion, out Stopwatch stopWatch)
    {
        var promptSettings = this._settings.GetPromptSettings(text, requestSettings, out isNewPrompt);
        textCompletion = promptSettings.SelectAppropriateTextCompletion(this._textCompletions, this._settings.ConnectorComparer);
        requestSettings = textCompletion.AdjustRequestSettings(text, requestSettings, this._logger);
        stopWatch = Stopwatch.StartNew();
        return promptSettings;
    }

    private async Task ApplyCreditorCostsAsync(string text, AsyncLazy<string> resultLazy, NamedTextCompletion textCompletion)
    {
        if (this.Creditor != null)
        {
            var result = await resultLazy.Value.ConfigureAwait(false);
            var cost = textCompletion.GetCost(text, result);
            this.Creditor.Credit(cost);
        }
    }

    /// <summary>
    /// Asynchronously collects results from a prompt call to evaluate connectors against the same prompt.
    /// </summary>
    private async Task CollectResultForTestAsync(string text, CompleteRequestSettings requestSettings, Stopwatch stopWatch, NamedTextCompletion textCompletion, AsyncLazy<string> resultLazy, CancellationToken cancellationToken)
    {
        var result = await resultLazy.Value.ConfigureAwait(false);

        stopWatch.Stop();
        var duration = stopWatch.Elapsed;

        // For the management task
        ConnectorTest connectorTest = ConnectorTest.Create(text, requestSettings, textCompletion, result, duration);
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
                var testSeries = new List<ConnectorTest>();

                while (this._connectorTestChannel.Reader.TryRead(out var connectorTest))
                {
                    if (!cancellationToken.IsCancellationRequested)
                    {
                        this._logger?.LogTrace(message: "OptimizeCompletionsAsync received a new ConnectorTest", connectorTest);
                        testSeries.Add(connectorTest);
                        await Task.Delay(this._settings.AnalysisSettings.AnalysisDelay, cancellationToken).ConfigureAwait(false);
                        this._logger?.LogTrace(message: "OptimizeCompletionsAsync waited analysis delay for new ConnectorTest", connectorTest);
                    }
                }

                this._logger?.LogTrace(message: "OptimizeCompletionsAsync collected a new ConnectorTest series to analyze", testSeries);
                // Evaluate the test

                var analysisResult = await this._settings.AnalysisSettings.EvaluatePromptConnectorsAsync(testSeries, this._textCompletions, this._settings, this._logger, cancellationToken).ConfigureAwait(false);

                // Raise the event after optimization is done
                this.OnOptimizationCompleted(analysisResult);
            }
        }
        catch (OperationCanceledException exception)
        {
            this._logger?.LogTrace("OptimizeCompletionsAsync Optimize task was cancelled with exception {0}", exception, exception.ToString());
        }
        catch (Exception exception)
        {
            this._logger?.LogError("OptimizeCompletionsAsync Optimize task failed with exception {0}", exception, exception.ToString());
            throw;
        }
    }

    // Define the event
    public event EventHandler<OptimizationCompletedEventArgs>? OptimizationCompleted;

    // Method to raise the event
    protected virtual void OnOptimizationCompleted(OptimizationCompletedEventArgs analysisResult)
    {
        this._logger?.LogTrace(message: "OptimizationCompleted event raised");
        this.OptimizationCompleted?.Invoke(this, analysisResult);
    }

    /// <summary>
    /// Appends a connector test to the test channel listened to in the Optimization long running task.
    /// </summary>
    private void AppendConnectorTest(ConnectorTest connectorTest)
    {
        this._logger?.LogTrace("Collecting new test with duration {0}, prompt {1}\nand result {2}", connectorTest.Duration, connectorTest.Prompt, connectorTest.Result);
        this._connectorTestChannel.Writer.TryWrite(connectorTest);
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
}

public class OptimizationCompletedEventArgs : EventArgs
{
    public MultiCompletionAnalysis Analysis { get; set; }
    public MultiTextCompletionSettings SuggestedSettings { get; set; }

    public OptimizationCompletedEventArgs(MultiCompletionAnalysis analysis, MultiTextCompletionSettings suggestedSettings)
    {
        this.Analysis = analysis;
        this.SuggestedSettings = suggestedSettings;
    }
}

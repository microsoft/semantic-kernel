// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

namespace SemanticKernel.Connectors.UnitTests.MultiConnector.TextCompletion;

public class ArithmeticCompletionService : ITextCompletion
{
    public ArithmeticCompletionService(MultiTextCompletionSettings multiTextCompletionSettings, List<ArithmeticOperation> supportedOperations, ArithmeticEngine engine, TimeSpan callTime, decimal costPerRequest, CallRequestCostCreditor creditor)
    {
        this.MultiTextCompletionSettings = multiTextCompletionSettings;
        this.SupportedOperations = supportedOperations;
        this.Engine = engine;
        this.CallTime = callTime;
        this.CostPerRequest = costPerRequest;
        this.Creditor = creditor;
        this.VettingPromptSettings = this.GenerateVettingSignature();
    }

    private PromptMultiConnectorSettings GenerateVettingSignature()
    {
        var tempOperation = ArithmeticEngine.GeneratePrompt(ArithmeticOperation.Add, 1, 1);
        var tempResult = "2";
        var vettingParams = this.MultiTextCompletionSettings.AnalysisSettings.GetVettingPrompt(tempOperation, tempResult);
        return this.MultiTextCompletionSettings.GetPromptSettings(vettingParams.vettingPrompt, vettingParams.vettingRequestSettings);
    }

    public PromptMultiConnectorSettings VettingPromptSettings { get; set; }

    public MultiTextCompletionSettings MultiTextCompletionSettings { get; set; }

    public List<ArithmeticOperation> SupportedOperations { get; set; }

    public ArithmeticEngine Engine { get; set; }

    public TimeSpan CallTime { get; set; }

    public decimal CostPerRequest { get; set; }

    public CallRequestCostCreditor Creditor { get; set; }

    public async Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(string text, CompleteRequestSettings requestSettings, CancellationToken cancellationToken = default)
    {
        ArithmeticStreamingResultBase streamingResult = await this.ComputeResultAsync(text, requestSettings, cancellationToken).ConfigureAwait(false);
        return new List<ITextResult>
        {
            streamingResult
        };
    }

    public async IAsyncEnumerable<ITextStreamingResult> GetStreamingCompletionsAsync(string text, CompleteRequestSettings requestSettings, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        ArithmeticStreamingResultBase streamingResult = await this.ComputeResultAsync(text, requestSettings, cancellationToken).ConfigureAwait(false);
        yield return streamingResult;
    }

    private async Task<ArithmeticStreamingResultBase> ComputeResultAsync(string text, CompleteRequestSettings requestSettings, CancellationToken cancellationToken = default)
    {
        await Task.Delay(this.CallTime, cancellationToken).ConfigureAwait(false);
        var isVetting = this.VettingPromptSettings.PromptType.Signature.Matches(text, requestSettings);
        ArithmeticStreamingResultBase streamingResult;
        if (isVetting)
        {
            streamingResult = new ArithmeticVettingStreamingResult(this.MultiTextCompletionSettings.AnalysisSettings, text, this.Engine, this.CallTime);
        }
        else
        {
            this.Creditor.Credit(this.CostPerRequest);
            streamingResult = new ArithmeticComputingStreamingResult(text, this.Engine, this.CallTime);
        }

        return streamingResult;
    }
}

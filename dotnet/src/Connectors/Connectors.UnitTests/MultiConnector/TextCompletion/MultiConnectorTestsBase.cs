// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.MultiConnector;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.Tokenizers;
using SemanticKernel.Connectors.UnitTests.MultiConnector.TextCompletion.ArithmeticMocks;
using Xunit.Abstractions;

namespace SemanticKernel.Connectors.UnitTests.MultiConnector.TextCompletion;

public class MultiConnectorTestsBase : IDisposable
{
    internal readonly XunitLogger<MultiTextCompletion> Logger;
    protected Func<string, int> DefaultTokenCounter { get; } = s => GPT3Tokenizer.Encode(s).Count;
    protected CancellationTokenSource CleanupToken { get; } = new();

    protected MultiConnectorTestsBase(ITestOutputHelper output)
    {
        this.Logger = new XunitLogger<MultiTextCompletion>(output);
    }

    protected List<NamedTextCompletion> CreateCompletions(MultiTextCompletionSettings settings, TimeSpan primaryCallDuration, decimal primaryCostPerRequest, TimeSpan secondaryCallDuration, decimal secondaryCostPerRequest, CallRequestCostCreditor? creditor)
    {
        var toReturn = new List<NamedTextCompletion>();

        //Build primary connectors with default multi-operation engine
        var primaryConnector = new ArithmeticCompletionService(settings,
            new List<ArithmeticOperation>() { ArithmeticOperation.Add, ArithmeticOperation.Divide, ArithmeticOperation.Multiply, ArithmeticOperation.Subtract },
            new(),
            primaryCallDuration,
            primaryCostPerRequest, creditor);
        var primaryCompletion = new NamedTextCompletion("Primary", primaryConnector)
        {
            CostPerRequest = primaryCostPerRequest,
            TokenCountFunc = this.DefaultTokenCounter
        };

        toReturn.Add(primaryCompletion);

        //Build secondary specialized connectors, specialized single-operation engine
        foreach (var operation in primaryConnector.SupportedOperations)
        {
            var secondaryConnector = new ArithmeticCompletionService(settings,
                new List<ArithmeticOperation>() { operation },
                new ArithmeticEngine()
                {
                    ComputeFunc = (arithmeticOperation, operand1, operand2) => ArithmeticEngine.Compute(operation, operand1, operand2)
                },
                secondaryCallDuration,
                secondaryCostPerRequest, creditor);
            var secondaryCompletion = new NamedTextCompletion($"Secondary - {operation}", secondaryConnector)
            {
                CostPerRequest = secondaryCostPerRequest,
                TokenCountFunc = this.DefaultTokenCounter
            };

            toReturn.Add(secondaryCompletion);
        }

        return toReturn;
    }

    // Create sample prompts
    protected CompletionJob[] CreateSampleJobs(ArithmeticOperation[] operations, int operand1, int operand2)
    {
        var requestSettings = new CompleteRequestSettings()
        {
            Temperature = 0,
            MaxTokens = 10
        };
        var prompts = operations.Select(op => ArithmeticEngine.GeneratePrompt(op, operand1, operand2)).ToArray();
        return prompts.Select(p => new CompletionJob(p, requestSettings)).ToArray();
    }

    protected static async Task<List<(string result, TimeSpan duration, decimal expectedCost)>> RunPromptsAsync(CompletionJob[] completionJobs, MultiTextCompletion multiConnector, Func<string, string, decimal> completionCostFunction)
    {
        List<(string result, TimeSpan duration, decimal expectedCost)> toReturn = new();
        foreach (var job in completionJobs)
        {
            var stopWatch = Stopwatch.StartNew();
            var result = await multiConnector.CompleteAsync(job.Prompt, job.RequestSettings).ConfigureAwait(false);
            stopWatch.Stop();
            var duration = stopWatch.Elapsed;
            var cost = completionCostFunction(job.Prompt, result);
            toReturn.Add((result, duration, cost));
        }

        return toReturn;
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    private bool _disposedValue;

    protected virtual void Dispose(bool disposing)
    {
        if (!this._disposedValue)
        {
            if (disposing)
            {
                this.CleanupToken.Cancel();
                this.CleanupToken.Dispose();
                this.Logger.Dispose();
            }

            this._disposedValue = true;
        }
    }
}

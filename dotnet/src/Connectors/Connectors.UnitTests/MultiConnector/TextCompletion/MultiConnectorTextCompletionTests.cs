// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.MultiConnector;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.Tokenizers;
using Microsoft.SemanticKernel.Orchestration;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Connectors.UnitTests.MultiConnector.TextCompletion;

public enum ArithmeticOperation
{
    Add,
    Subtract,
    Multiply,
    Divide
}

public class ArithmeticEngine
{
    public Func<ArithmeticOperation, int, int, int> ComputeFunc { get; set; } = Compute;

    public static int Compute(ArithmeticOperation operation, int operand1, int operand2)
    {
        return operation switch
        {
            ArithmeticOperation.Add => operand1 + operand2,
            ArithmeticOperation.Subtract => operand1 - operand2,
            ArithmeticOperation.Multiply => operand1 * operand2,
            ArithmeticOperation.Divide => operand1 / operand2,
            _ => throw new ArgumentOutOfRangeException(nameof(operation))
        };
    }

    public static string GeneratePrompt(ArithmeticOperation operation, int operand1, int operand2)
    {
        return $"Compute {operation}({operand1.ToString(CultureInfo.InvariantCulture)}, {operand2.ToString(CultureInfo.InvariantCulture)})";
    }

    public static (ArithmeticOperation operation, int operand1, int operand2) ParsePrompt(string prompt)
    {
        var match = Regex.Match(prompt, @"Compute (?<operation>.*)\((?<operand1>\d+), (?<operand2>\d+)\)");

        if (!match.Success)
        {
            throw new ArgumentException("Invalid prompt format.", nameof(prompt));
        }

        var operation = Enum.Parse<ArithmeticOperation>(match.Groups["operation"].Value);
        var operand1 = int.Parse(match.Groups["operand1"].Value, CultureInfo.InvariantCulture);
        var operand2 = int.Parse(match.Groups["operand2"].Value, CultureInfo.InvariantCulture);

        return (operation, operand1, operand2);
    }

    public string Run(string prompt)
    {
        var operation = ParsePrompt(prompt);
        return $"{this.ComputeFunc(operation.operation, operation.operand1, operation.operand2).ToString(CultureInfo.InvariantCulture)}";
    }
}

public class CallRequestCostCreditor
{
    private decimal _ongoingCost;

    public decimal OngoingCost
    {
        get => this._ongoingCost;
    }

    public void Reset()
    {
        this._ongoingCost = 0;
    }

    public void Credit(decimal cost)
    {
        this._ongoingCost += cost;
    }
}

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

public abstract class ArithmeticStreamingResultBase : ITextStreamingResult
{
    private ModelResult? _modelResult;

    public ModelResult ModelResult => this._modelResult ?? this.GenerateModelResult().Result;

    protected abstract Task<ModelResult> GenerateModelResult();

    public async Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        this._modelResult = await this.GenerateModelResult();
        return this.ModelResult?.GetResult<string>() ?? string.Empty;
    }

    public async IAsyncEnumerable<string> GetCompletionStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this._modelResult = await this.GenerateModelResult();

        string resultText = this.ModelResult.GetResult<string>();
        // Your model logic here
        var streamedOutput = resultText.Split(' ');
        foreach (string word in streamedOutput)
        {
            yield return $"{word} ";
        }
    }
}

public class ArithmeticVettingStreamingResult : ArithmeticStreamingResultBase
{
    private readonly string _prompt;
    private ArithmeticEngine _engine;
    private readonly MultiCompletionAnalysisSettings _analysisSettings;

    public ArithmeticVettingStreamingResult(MultiCompletionAnalysisSettings analysisSettings, string prompt, ArithmeticEngine engine, TimeSpan callTime) : base()
    {
        this._analysisSettings = analysisSettings;
        this._prompt = prompt;
        this._engine = engine;
    }

    protected async override Task<ModelResult> GenerateModelResult()
    {
        try
        {
            var analysisComponents = this._analysisSettings.CaptureVettingPromptComponents(this._prompt);

            var operation = ArithmeticEngine.ParsePrompt(analysisComponents.prompt);
            var correctResult = ArithmeticEngine.Compute(operation.operation, operation.operand1, operation.operand2);
            var connectorResult = int.Parse(analysisComponents.response, CultureInfo.InvariantCulture);

            var result = (correctResult == connectorResult).ToString(CultureInfo.InvariantCulture);

            return new ModelResult(result);
        }
        catch (Exception e)
        {
            Console.WriteLine(e);
            throw;
        }
    }
}

public class ArithmeticComputingStreamingResult : ArithmeticStreamingResultBase
{
    private readonly string _prompt;
    private readonly ArithmeticEngine _engine;

    public ArithmeticComputingStreamingResult(string prompt, ArithmeticEngine engine, TimeSpan callTime) : base()
    {
        this._prompt = prompt;
        this._engine = engine;
    }

    protected async override Task<ModelResult> GenerateModelResult()
    {
        var result = this._engine.Run(this._prompt);
        return new ModelResult(result);
    }
}

/// <summary>
/// Unit tests for <see cref="MultiTextCompletion"/> class.
/// </summary>
public sealed class MultiConnectorTextCompletionTests : IDisposable
{
    private readonly XunitLogger<MultiTextCompletion> _logger;

    private readonly Func<string, int> _defaultTokenCounter = s => GPT3Tokenizer.Encode(s).Count;

    public MultiConnectorTextCompletionTests(ITestOutputHelper output)
    {
        this._logger = new XunitLogger<MultiTextCompletion>(output);
    }

    private List<NamedTextCompletion> CreateCompletions(MultiTextCompletionSettings settings, TimeSpan primaryCallDuration, decimal primaryCostPerRequest, TimeSpan secondaryCallDuration, decimal secondaryCostPerRequest, CallRequestCostCreditor creditor)
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
            TokenCountFunc = this._defaultTokenCounter
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
                TokenCountFunc = this._defaultTokenCounter
            };

            toReturn.Add(secondaryCompletion);
        }

        return toReturn;
    }

    /// <summary>
    /// In this theory, we test that the multi-connector analysis is able to optimize the cost per request and duration of a multi-connector completion, with a primary connector capable of handling all 4 arithmetic operation, and secondary connectors only capable of performing 1 each. Depending on their respective performances in parameters and the respective weights of duration and cost in the analysis settings, the multi-connector analysis should be able to determine the best connector to account for the given preferences.
    /// </summary>
    [Theory]
    [InlineData(3, 0.02, 1, 0.01, 1, 1, 0.01, 3)]
    [InlineData(2, 0.02, 1, 0.1, 1, 1, 0.02, 1)]
    [InlineData(2, 0.02, 1, 0.1, 1, 0, 0.1, 2)]
    public async Task MultiConnectorAnalysisShouldDecreaseCostsAsync(int primaryCallDuration = 2, decimal primaryCostPerRequest = 0.02m, int secondaryCallDuration = 1,
        decimal secondaryCostPerRequest = 0.01m,
        double durationWeight = 1,
        double costWeight = 1,
        decimal expectedCostPerRequest = 0.01m,
        double expectedDurationGain = 2)
    {
        //Arrange

        //We configure settings to enable analysis, and let the connector discover the best settings, updating on the fly and deleting analysis file 
        var settings = new MultiTextCompletionSettings()
        {
            AnalysisSettings = new MultiCompletionAnalysisSettings()
            {
                EnableAnalysis = true,
                NbPromptTests = 3,
                AnalysisPeriod = TimeSpan.FromMilliseconds(10),
                AnalysisDelay = TimeSpan.FromMilliseconds(10),
                UpdateSuggestedSettings = true,
                DeleteAnalysisFile = true,
                SaveSuggestedSettings = false
            },
            PromptTruncationLength = 11,
            ConnectorComparer = MultiTextCompletionSettings.GetConnectorComparer(durationWeight, costWeight)
        };

        // We configure a primary completion with default performances and cost, secondary completion have a gain of 2 in performances and in cost, but they can only handle a single operation each

        var creditor = new CallRequestCostCreditor();

        var completions = this.CreateCompletions(settings, TimeSpan.FromMilliseconds(primaryCallDuration), primaryCostPerRequest, TimeSpan.FromMilliseconds(secondaryCallDuration), secondaryCostPerRequest, creditor);

        var prompts = Enum.GetValues(typeof(ArithmeticOperation)).Cast<ArithmeticOperation>().Select(arithmeticOperation => ArithmeticEngine.GeneratePrompt(arithmeticOperation, 8, 2)).ToArray();

        var requestSettings = new CompleteRequestSettings()
        {
            Temperature = 0,
            MaxTokens = 10
        };

        var multiConnector = new MultiTextCompletion(settings, completions[0], CancellationToken.None, this._logger, completions.Skip(1).ToArray());

        // Create a task completion source to signal the completion of the optimization
        var optimizationCompletedTaskSource = new TaskCompletionSource<bool>();

        // Subscribe to the OptimizationCompleted event
        multiConnector.OptimizationCompleted += (sender, args) =>
        {
            // Signal the completion of the optimization
            optimizationCompletedTaskSource.SetResult(true);
        };

        //Act

        var primaryResults = await RunPromptsAsync(prompts, multiConnector, requestSettings, completions[0].GetCost).ConfigureAwait(false);

        var firstPassEffectiveCost = creditor.OngoingCost;
        decimal firstPassExpectedCost = primaryResults.Sum(tuple => tuple.expectedCost);
        //We remove the first prompt in time measurement because it is longer on first pass due to warmup
        var firstPassDurationAfterWarmup = TimeSpan.FromTicks(primaryResults.Skip(1).Sum(tuple => tuple.duration.Ticks));

        // Wait for the optimization to complete
        await optimizationCompletedTaskSource.Task;

        creditor.Reset();

        // Redo the same requests with the new settings
        var secondaryResults = await RunPromptsAsync(prompts, multiConnector, requestSettings, (s, s1) => expectedCostPerRequest).ConfigureAwait(false);
        decimal secondPassExpectedCost = secondaryResults.Sum(tuple => tuple.expectedCost);
        var secondPassEffectiveCost = creditor.OngoingCost;

        //We also remove the first prompt in time measurement on second pass to align comparison

        var secondPassDurationAfterWarmup = TimeSpan.FromTicks(secondaryResults.Skip(1).Sum(tuple => tuple.duration.Ticks));

        // Assert

        for (int index = 0; index < prompts.Length; index++)
        {
            string? prompt = prompts[index];
            var parsed = ArithmeticEngine.ParsePrompt(prompt);
            var realResult = ArithmeticEngine.Compute(parsed.operation, parsed.operand1, parsed.operand2).ToString(CultureInfo.InvariantCulture);
            Assert.Equal(realResult, primaryResults[index].result);
            Assert.Equal(realResult, secondaryResults[index].result);
        }

        Assert.Equal(firstPassExpectedCost, firstPassEffectiveCost);

        Assert.Equal(secondPassExpectedCost, secondPassEffectiveCost);

        Assert.InRange(secondPassDurationAfterWarmup, firstPassDurationAfterWarmup / (expectedDurationGain * 2), firstPassDurationAfterWarmup / (expectedDurationGain / 2));
    }

    private static async Task<List<(string result, TimeSpan duration, decimal expectedCost)>> RunPromptsAsync(string[] prompts, MultiTextCompletion multiConnector, CompleteRequestSettings promptRequestSettings, Func<string, string, decimal> completionCostFunction)
    {
        List<(string result, TimeSpan duration, decimal expectedCost)> toReturn = new();
        foreach (var prompt in prompts)
        {
            var stopWatch = Stopwatch.StartNew();
            var result = await multiConnector.CompleteAsync(prompt, promptRequestSettings).ConfigureAwait(false);
            stopWatch.Stop();
            var duration = stopWatch.Elapsed;
            var cost = completionCostFunction(prompt, result);
            toReturn.Add((result, duration, cost));
        }

        return toReturn;
    }

    public void Dispose()
    {
        this._logger.Dispose();
    }
}

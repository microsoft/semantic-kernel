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
        this.Creditor.Credit(this.CostPerRequest);
        ArithmeticStreamingResultBase streamingResult = await this.ComputeResultAsync(text, requestSettings, cancellationToken).ConfigureAwait(false);
        return new List<ITextResult>
        {
            streamingResult
        };
    }

    public async IAsyncEnumerable<ITextStreamingResult> GetStreamingCompletionsAsync(string text, CompleteRequestSettings requestSettings, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this.Creditor.Credit(this.CostPerRequest);
        ArithmeticStreamingResultBase streamingResult = await this.ComputeResultAsync(text, requestSettings, cancellationToken).ConfigureAwait(false);
        yield return streamingResult;
    }

    private async Task<ArithmeticStreamingResultBase> ComputeResultAsync(string text, CompleteRequestSettings requestSettings, CancellationToken cancellationToken = default)
    {
        await Task.Delay(this.CallTime, cancellationToken);
        var isVetting = this.VettingPromptSettings.PromptType.Signature.Matches(text, requestSettings);
        ArithmeticStreamingResultBase streamingResult;
        if (isVetting)
        {
            streamingResult = new ArithmeticVettingStreamingResult(this.MultiTextCompletionSettings.AnalysisSettings, text, this.Engine, this.CallTime);
        }
        else
        {
            streamingResult = new ArithmeticComputingStreamingResult(text, this.Engine, this.CallTime);
        }

        return streamingResult;
    }
}

public abstract class ArithmeticStreamingResultBase : ITextStreamingResult
{
    private ModelResult? _modelResult;
    private readonly TimeSpan _callTime;

    protected ArithmeticStreamingResultBase(TimeSpan callTime)
    {
        this._callTime = callTime;
    }

    public ModelResult ModelResult => this._modelResult ?? this.GenerateModelResult();

    protected abstract ModelResult GenerateModelResult();

    public async Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        await Task.Delay(this._callTime, cancellationToken);
        this._modelResult = this.GenerateModelResult();
        return this.ModelResult?.GetResult<string>() ?? string.Empty;
    }

    public async IAsyncEnumerable<string> GetCompletionStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this._modelResult = this.GenerateModelResult();

        string resultText = this.ModelResult.GetResult<string>();
        // Your model logic here
        var streamedOutput = resultText.Split(' ');
        var streamDelay = this._callTime.TotalMilliseconds / streamedOutput.Length;
        var streamDelayTimeSpan = TimeSpan.FromMilliseconds(streamDelay);
        foreach (string word in streamedOutput)
        {
            await Task.Delay(streamDelayTimeSpan, cancellationToken);
            yield return $"{word} ";
        }
    }
}

public class ArithmeticVettingStreamingResult : ArithmeticStreamingResultBase
{
    private readonly string _prompt;
    private ArithmeticEngine _engine;
    private readonly MultiCompletionAnalysisSettings _analysisSettings;

    public ArithmeticVettingStreamingResult(MultiCompletionAnalysisSettings analysisSettings, string prompt, ArithmeticEngine engine, TimeSpan callTime) : base(callTime)
    {
        this._analysisSettings = analysisSettings;
        this._prompt = prompt;
        this._engine = engine;
    }

    protected override ModelResult GenerateModelResult()
    {
        var analysisComponents = this._analysisSettings.CaptureVettingPromptComponents(this._prompt);

        var operation = ArithmeticEngine.ParsePrompt(analysisComponents.prompt);
        var correctResult = ArithmeticEngine.Compute(operation.operation, operation.operand1, operation.operand2);
        var connectorResult = int.Parse(analysisComponents.response, CultureInfo.InvariantCulture);

        var result = (correctResult == connectorResult).ToString(CultureInfo.InvariantCulture);

        return new ModelResult(result);
    }
}

public class ArithmeticComputingStreamingResult : ArithmeticStreamingResultBase
{
    private readonly string _prompt;
    private readonly ArithmeticEngine _engine;

    public ArithmeticComputingStreamingResult(string prompt, ArithmeticEngine engine, TimeSpan callTime) : base(callTime)
    {
        this._prompt = prompt;
        this._engine = engine;
    }

    protected override ModelResult GenerateModelResult()
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

        var engine = new ArithmeticEngine();
        var primaryConnector = new ArithmeticCompletionService(settings,
            new List<ArithmeticOperation>() { ArithmeticOperation.Add, ArithmeticOperation.Divide, ArithmeticOperation.Multiply, ArithmeticOperation.Subtract },
            engine,
            primaryCallDuration,
            primaryCostPerRequest, creditor);
        var primaryCompletion = new NamedTextCompletion("Primary", primaryConnector)
        {
            CostPerRequest = primaryCostPerRequest,
            TokenCountFunc = this._defaultTokenCounter
        };

        toReturn.Add(primaryCompletion);

        foreach (var operation in primaryConnector.SupportedOperations)
        {
            //Build secondary specialized connectors
            engine = new ArithmeticEngine()
            {
                ComputeFunc = (arithmeticOperation, operand1, operand2) => ArithmeticEngine.Compute(operation, operand1, operand2)
            };
            var secondaryConnector = new ArithmeticCompletionService(settings,
                new List<ArithmeticOperation>() { operation },
                engine,
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

    [Fact]
    public async Task MultiConnectorAnalysisShouldDecreaseCostsAsync()
    {
        CancellationToken cancellationToken = default;

        var settings = new MultiTextCompletionSettings()
        {
            AnalysisSettings = new MultiCompletionAnalysisSettings()
            {
                EnableAnalysis = true,
                AnalysisPeriod = TimeSpan.FromTicks(1),
                UpdateSuggestedSettings = true,
            },
            PromptTruncationLength = 11
        };

        var gainRatio = 2;
        var primaryCallDuration = TimeSpan.FromMilliseconds(100);
        var primaryCostPerRequest = 0.1m;
        var secondaryCallDuration = primaryCallDuration / gainRatio;
        var secondaryCostPerRequest = primaryCostPerRequest / gainRatio;
        var creditor = new CallRequestCostCreditor();
        //Arrange
        var completions = this.CreateCompletions(settings, primaryCallDuration, primaryCostPerRequest, secondaryCallDuration, secondaryCostPerRequest, creditor);

        var prompts = Enum.GetValues(typeof(ArithmeticOperation)).Cast<ArithmeticOperation>().Select(arithmeticOperation => ArithmeticEngine.GeneratePrompt(arithmeticOperation, 8, 2)).ToArray();

        var requestSettings = new CompleteRequestSettings()
        {
            Temperature = 0,
            MaxTokens = 10
        };

        //Act

        var multiConnector = new MultiTextCompletion(settings, completions[0], CancellationToken.None, this._logger, completions.Skip(1).ToArray());

        var stopWatch = new Stopwatch();

        var promptResultsPrimary = new List<(string result, TimeSpan duration, decimal cost)>();

        var primaryResults = await RunPromptsAsync(prompts, stopWatch, multiConnector, requestSettings, completions[0].GetCost);

        stopWatch.Stop();
        var elapsed = stopWatch.Elapsed;

        var primaryCreditorOngoingCost = creditor.OngoingCost;
        creditor.Reset();

        //Wait for analysis to complete
        await Task.Delay(50, cancellationToken);

        // Redo the same requests with the new settings
        var secondaryResults = await RunPromptsAsync(prompts, stopWatch, multiConnector, requestSettings, completions[1].GetCost);

        var secondCreditorOngoingCost = creditor.OngoingCost;

        //Assert

        for (int index = 0; index < prompts.Length; index++)
        {
            string? prompt = prompts[index];
            var parsed = ArithmeticEngine.ParsePrompt(prompt);
            var realResult = ArithmeticEngine.Compute(parsed.operation, parsed.operand1, parsed.operand2).ToString(CultureInfo.InvariantCulture);
            Assert.Equal(realResult, primaryResults[index].result);
            Assert.Equal(realResult, secondaryResults[index].result);
        }

        Assert.Equal(primaryResults.Sum(tuple => tuple.expectedCost), primaryCreditorOngoingCost);
        Assert.Equal(secondaryResults.Sum(tuple => tuple.expectedCost), secondCreditorOngoingCost);
    }

    private static async Task<List<(string result, TimeSpan duration, decimal expectedCost)>> RunPromptsAsync(string[] prompts, Stopwatch stopWatch, MultiTextCompletion multiConnector, CompleteRequestSettings promptRequestSettings, Func<string, string, decimal> completionCostFunction)
    {
        List<(string result, TimeSpan duration, decimal expectedCost)> toReturn = new();
        foreach (var prompt in prompts)
        {
            stopWatch.Reset();
            stopWatch.Start();
            var result = await multiConnector.CompleteAsync(prompt, promptRequestSettings);
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

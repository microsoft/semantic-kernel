// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.MultiConnector;
using Microsoft.SemanticKernel.Connectors.AI.MultiConnector.Analysis;
using SemanticKernel.Connectors.UnitTests.MultiConnector.TextCompletion.ArithmeticMocks;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Connectors.UnitTests.MultiConnector.TextCompletion;

/// <summary>
/// Unit tests for <see cref="MultiTextCompletion"/> class.
/// </summary>
public sealed class MultiConnectorTextCompletionTests : MultiConnectorTestsBase
{
    public MultiConnectorTextCompletionTests(ITestOutputHelper output) : base(output)
    {
    }

    [Fact]
    public void CreateCompletionsShouldReturnCorrectCompletions()
    {
        var settings = new MultiTextCompletionSettings();
        var completions = this.CreateCompletions(settings, TimeSpan.FromMilliseconds(10), 0.02m, TimeSpan.FromMilliseconds(5), 0.01m, new CallRequestCostCreditor());
        Assert.Equal(5, completions.Count);
        Assert.Equal("Primary", completions.First().Name);
        var secondaryCompletion = completions.Skip(1).First();
        Assert.StartsWith("Secondary", secondaryCompletion.Name, StringComparison.OrdinalIgnoreCase);
    }

    [Theory]
    [InlineData(ArithmeticOperation.Add, 5, 3, 8)]
    [InlineData(ArithmeticOperation.Subtract, 5, 3, 2)]
    public async Task ArithmeticCompletionServiceShouldPerformOperationCorrectlyAsync(ArithmeticOperation operation, int operand1, int operand2, int expectedResult)
    {
        // Arrange
        var settings = new MultiTextCompletionSettings();
        var operations = new List<ArithmeticOperation>() { operation };
        var service = new ArithmeticCompletionService(settings, operations, new ArithmeticEngine(), TimeSpan.Zero, 0m, null);
        var prompt = ArithmeticEngine.GeneratePrompt(operation, operand1, operand2);

        // Act
        var result = await service.CompleteAsync(prompt, new CompleteRequestSettings());

        // Assert
        Assert.Equal(expectedResult.ToString(CultureInfo.InvariantCulture), result);
    }

    [Theory]
    [InlineData("Compute Add(5, 3)", ArithmeticOperation.Add, 5, 3)]
    [InlineData("Compute Subtract(8, 2)", ArithmeticOperation.Subtract, 8, 2)]
    public void ArithmeticEngineShouldParsePromptCorrectly(string prompt, ArithmeticOperation expectedOperation, int expectedOperand1, int expectedOperand2)
    {
        // Act
        var parsed = ArithmeticEngine.ParsePrompt(prompt);

        // Assert
        Assert.Equal(expectedOperation, parsed.operation);
        Assert.Equal(expectedOperand1, parsed.operand1);
        Assert.Equal(expectedOperand2, parsed.operand2);
    }

    [Fact]
    public async Task MultiCompletionUsesDefaultPrimaryAssignsCostAsync()
    {
        var creditor = new CallRequestCostCreditor();
        // Arrange
        var settings = new MultiTextCompletionSettings() { EnablePromptSampling = false, Creditor = creditor };
        decimal expectedCost = 0.02m;

        int operand1 = 8;
        int operand2 = 4;
        var completionJobs = this.CreateSampleJobs(new[] { ArithmeticOperation.Multiply }, operand1, operand2);

        // Act
        var completions = this.CreateCompletions(settings, TimeSpan.Zero, expectedCost, TimeSpan.Zero, 0m, null);
        var primaryCompletion = completions.First();

        var multiConnector = new MultiTextCompletion(settings, completions[0], CancellationToken.None, logger: this.Logger, otherCompletions: completions.Skip(1).ToArray());

        var primaryResults = await RunPromptsAsync(completionJobs, multiConnector, completions[0].GetCost).ConfigureAwait(false);

        var effectiveCost = creditor.OngoingCost;

        // Assert
        Assert.Equal(expectedCost, primaryCompletion.CostPerRequest);

        Assert.Equal(1, primaryResults.Count);
        Assert.Equal((operand1 * operand2).ToString(CultureInfo.InvariantCulture), primaryResults.First().result);
        Assert.Equal(expectedCost, effectiveCost);
    }

    /// <summary>
    /// In this theory, we test that the multi-connector analysis is able to optimize the cost per request and duration of a multi-connector completion, with a primary connector capable of handling all 4 arithmetic operation, and secondary connectors only capable of performing 1 each. Depending on their respective performances in parameters and the respective weights of duration and cost in the analysis settings, the multi-connector analysis should be able to determine the best connector to account for the given preferences.
    /// </summary>
    [Theory]
    [InlineData(20, 0.02, 2, 0.01, 1, 1, 0.01, 10)]
    [InlineData(20, 0.02, 2, 0.1, 1, 1, 0.02, 1)]
    [InlineData(20, 0.02, 2, 0.1, 1, 0, 0.1, 10)]
    public async Task MultiConnectorAnalysisShouldDecreaseCostsAsync(int primaryDuration = 2, decimal primaryCost = 0.02m, int secondaryDuration = 1,
        decimal secondaryCost = 0.01m,
        double durationWeight = 1,
        double costWeight = 1,
        decimal expectedCost = 0.01m,
        double expectedPerfGain = 2)
    {
        //Arrange

        //We configure settings to enable analysis, and let the connector discover the best settings, updating on the fly and deleting analysis file 
        var settings = new MultiTextCompletionSettings()
        {
            AnalysisSettings = new MultiCompletionAnalysisSettings()
            {
                EnableAnalysis = true,
                NbPromptTests = 3,
                AnalysisAwaitsManualTrigger = true,
                AnalysisDelay = TimeSpan.Zero,
                TestsPeriod = TimeSpan.Zero,
                EvaluationPeriod = TimeSpan.Zero,
                SuggestionPeriod = TimeSpan.Zero,
                UpdateSuggestedSettings = true,
                //Uncomment the following lines for additional debugging information
                DeleteAnalysisFile = false,
                SaveSuggestedSettings = true
            },
            PromptTruncationLength = 11,
            ConnectorComparer = MultiTextCompletionSettings.GetWeightedConnectorComparer(durationWeight, costWeight),
            // Uncomment to enable additional logging of MultiTextCompletion calls, results and/or test sample collection
            LogCallResult = true,
            //LogTestCollection = true,
        };

        // Cleanup in case the previous test failed to delete the analysis file
        if (File.Exists(settings.AnalysisSettings.AnalysisFilePath))
        {
            File.Delete(settings.AnalysisSettings.AnalysisFilePath);

            this.Logger.LogTrace("Deleted preexisting analysis file: {0}", settings.AnalysisSettings.AnalysisFilePath);
        }

        // We configure a primary completion with default performances and cost, secondary completion have a gain of 2 in performances and in cost, but they can only handle a single operation each

        var creditor = new CallRequestCostCreditor();

        var completions = this.CreateCompletions(settings, TimeSpan.FromMilliseconds(primaryDuration), primaryCost, TimeSpan.FromMilliseconds(secondaryDuration), secondaryCost, creditor);

        var completionJobs = this.CreateSampleJobs(Enum.GetValues(typeof(ArithmeticOperation)).Cast<ArithmeticOperation>().ToArray(), 8, 2);

        var multiConnector = new MultiTextCompletion(settings, completions[0], this.CleanupToken.Token, logger: this.Logger, otherCompletions: completions.Skip(1).ToArray());

        // Create a task completion source to signal the completion of the optimization
        var optimizationCompletedTaskSource = new TaskCompletionSource<SuggestionCompletedEventArgs>();

        // Subscribe to the OptimizationCompleted event
        settings.AnalysisSettings.SuggestionCompleted += (sender, args) =>
        {
            // Signal the completion of the optimization
            optimizationCompletedTaskSource.SetResult(args);
        };

        // Subscribe to the OptimizationCompleted event
        settings.AnalysisSettings.AnalysisTaskCrashed += (sender, args) =>
        {
            // Signal the completion of the optimization
            optimizationCompletedTaskSource.SetException(args.CrashEvent.Exception);
        };

        //Act

        var primaryResults = await RunPromptsAsync(completionJobs, multiConnector, completions[0].GetCost).ConfigureAwait(false);

        var firstPassEffectiveCost = creditor.OngoingCost;
        decimal firstPassExpectedCost = primaryResults.Sum(tuple => tuple.expectedCost);
        //We remove the first prompt in time measurement because it is longer on first pass due to warmup
        var firstPassDurationAfterWarmup = TimeSpan.FromTicks(primaryResults.Skip(1).Sum(tuple => tuple.duration.Ticks));

        // We disable prompt sampling to ensure no other tests are generated
        settings.EnablePromptSampling = false;

        // release optimization task
        settings.AnalysisSettings.AnalysisAwaitsManualTrigger = false;
        settings.AnalysisSettings.ReleaseAnalysisTasks();
        // Get the optimization results
        var optimizationResults = await optimizationCompletedTaskSource.Task.ConfigureAwait(false);

        creditor.Reset();

        // Redo the same requests with the new settings
        var secondaryResults = await RunPromptsAsync(completionJobs, multiConnector, (s, s1) => expectedCost).ConfigureAwait(false);
        decimal secondPassExpectedCost = secondaryResults.Sum(tuple => tuple.expectedCost);
        var secondPassEffectiveCost = creditor.OngoingCost;

        //We also remove the first prompt in time measurement on second pass to align comparison

        var secondPassDurationAfterWarmup = TimeSpan.FromTicks(secondaryResults.Skip(1).Sum(tuple => tuple.duration.Ticks));

        // Assert

        for (int index = 0; index < completionJobs.Length; index++)
        {
            string? prompt = completionJobs[index].Prompt;
            var parsed = ArithmeticEngine.ParsePrompt(prompt);
            var realResult = ArithmeticEngine.Compute(parsed.operation, parsed.operand1, parsed.operand2).ToString(CultureInfo.InvariantCulture);
            Assert.Equal(realResult, primaryResults[index].result);
            Assert.Equal(realResult, secondaryResults[index].result);
        }

        Assert.Equal(firstPassExpectedCost, firstPassEffectiveCost);

        Assert.Equal(secondPassExpectedCost, secondPassEffectiveCost);

        //We measure time ratio very approximately because it may depend on the machine load
        Assert.InRange(secondPassDurationAfterWarmup, firstPassDurationAfterWarmup / (expectedPerfGain * 3), firstPassDurationAfterWarmup / (expectedPerfGain / 3));
    }
}

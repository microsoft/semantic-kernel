// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AI.MultiConnector;
using Microsoft.SemanticKernel.Orchestration;

namespace SemanticKernel.Connectors.UnitTests.MultiConnector.TextCompletion;

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

    protected override Task<ModelResult> GenerateModelResult()
    {
        try
        {
            var analysisComponents = this._analysisSettings.CaptureVettingPromptComponents(this._prompt);

            var operation = ArithmeticEngine.ParsePrompt(analysisComponents.prompt);
            var correctResult = ArithmeticEngine.Compute(operation.operation, operation.operand1, operation.operand2);
            var connectorResult = int.Parse(analysisComponents.response, CultureInfo.InvariantCulture);

            var result = (correctResult == connectorResult).ToString(CultureInfo.InvariantCulture);

            return Task.FromResult(new ModelResult(result));
        }
        catch (Exception e)
        {
            Console.WriteLine(e);
            throw;
        }
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.PowerFx;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows.PowerFx;
using Xunit;

namespace Microsoft.SemanticKernel.Process.UnitTests.Workflows;

#pragma warning disable CA1308 // Ignore "Normalize strings to uppercase" warning for test cases

public sealed class RecalcEngineTests
{
    [Fact]
    public void EvaluateConstant()
    {
        RecalcEngine engine = RecalcEngineFactory.Create([], 100);

        this.EvaluateExpression(engine, 0m, "0");
        this.EvaluateExpression(engine, -1m, "-1");
        this.EvaluateExpression(engine, true, "true");
        this.EvaluateExpression(engine, false, "false");
        this.EvaluateExpression(engine, (string?)null, string.Empty);
        this.EvaluateExpression(engine, "Hi", "\"Hi\"");
    }

    [Fact]
    public void EvaluateInvalid()
    {
        RecalcEngine engine = RecalcEngineFactory.Create([], 100);
        engine.UpdateVariable("Scoped.Value", DecimalValue.New(33));

        this.EvaluateFailure(engine, "Hi");
        this.EvaluateFailure(engine, "True");
        this.EvaluateFailure(engine, "TRUE");
        this.EvaluateFailure(engine, "=1", canParse: false);
        this.EvaluateFailure(engine, "=1+2", canParse: false);
        this.EvaluateFailure(engine, "CustomValue");
        this.EvaluateFailure(engine, "CustomValue + 1");
        this.EvaluateFailure(engine, "Scoped.Value");
        this.EvaluateFailure(engine, "Scoped.Value + 1");
        this.EvaluateFailure(engine, "\"BEGIN-\" & Scoped.Value & \"-END\"");
    }

    [Fact]
    public void EvaluateFormula()
    {
        NamedValue[] recordValues =
            [
                new NamedValue("Label", StringValue.New("Test")),
                new NamedValue("Value", DecimalValue.New(54)),
            ];
        FormulaValue complexValue = FormulaValue.NewRecordFromFields(recordValues);

        RecalcEngine engine = RecalcEngineFactory.Create([], 100);
        engine.UpdateVariable("CustomLabel", StringValue.New("Note"));
        engine.UpdateVariable("CustomValue", DecimalValue.New(42));
        engine.UpdateVariable("Scoped", complexValue);

        this.EvaluateExpression(engine, 2m, "1 + 1");
        this.EvaluateExpression(engine, 42m, "CustomValue");
        this.EvaluateExpression(engine, 43m, "CustomValue + 1");
        this.EvaluateExpression(engine, "Note", "CustomLabel");
        //this.EvaluateExpression(engine, "Note", "\"{CustomLabel}\"");
        this.EvaluateExpression(engine, "BEGIN-42-END", "\"BEGIN-\" & CustomValue & \"-END\"");
        this.EvaluateExpression(engine, 54m, "Scoped.Value");
        this.EvaluateExpression(engine, 55m, "Scoped.Value + 1");
        this.EvaluateExpression(engine, "Test", "Scoped.Label");
        //this.EvaluateExpression(engine, "Test", "\"{Scoped.Label}\"");
    }

    private void EvaluateFailure(RecalcEngine engine, string sourceExpression, bool canParse = true)
    {
        CheckResult checkResult = engine.Check(sourceExpression);
        Assert.False(checkResult.IsSuccess);
        ParseResult parseResult = engine.Parse(sourceExpression);
        Assert.Equal(canParse, parseResult.IsSuccess);
        Assert.Throws<AggregateException>(() => engine.Eval(sourceExpression));
    }

    private void EvaluateExpression<T>(RecalcEngine engine, T expectedResult, string sourceExpression)
    {
        CheckResult checkResult = engine.Check(sourceExpression);
        Assert.True(checkResult.IsSuccess);
        ParseResult parseResult = engine.Parse(sourceExpression);
        Assert.True(parseResult.IsSuccess);
        FormulaValue valueResult = engine.Eval(sourceExpression);
        if (expectedResult is null)
        {
            Assert.Null(valueResult.ToObject());
        }
        else
        {
            Assert.IsType<T>(valueResult.ToObject());
            Assert.Equal(expectedResult, valueResult.ToObject());
        }
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Text.Json;
using Microsoft.Bot.ObjectModel;
using Microsoft.Bot.ObjectModel.Abstractions;
using Microsoft.Bot.ObjectModel.Exceptions;
using Microsoft.PowerFx;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows.Extensions;

namespace Microsoft.SemanticKernel.Process.Workflows.PowerFx;

internal class FoundryExpressionEngine : IExpressionEngine
{
    private static readonly JsonSerializerOptions s_options = new(); // %%% INVESTIGATE: ElementSerializer.CreateOptions();

    private readonly RecalcEngine _engine;

    public FoundryExpressionEngine(RecalcEngine engine)
    {
        this._engine = engine;
    }

    public EvaluationResult<bool> GetValue(BoolExpression boolean, ProcessActionScopes state) => this.GetValue(boolean, state, this.EvaluateScope);

    public EvaluationResult<bool> GetValue(BoolExpression boolean, RecordDataValue state) => this.GetValue(boolean, state, this.EvaluateState);

    public EvaluationResult<string> GetValue(StringExpression expression, ProcessActionScopes state) => this.GetValue(expression, state, this.EvaluateScope);

    public EvaluationResult<string> GetValue(StringExpression expression, RecordDataValue state) => this.GetValue(expression, state, this.EvaluateState);

    public EvaluationResult<DataValue> GetValue(ValueExpression expression, ProcessActionScopes state) => this.GetValue(expression, state, this.EvaluateScope);

    public EvaluationResult<DataValue> GetValue(ValueExpression expression, RecordDataValue state) => this.GetValue(expression, state, this.EvaluateState);

    public EvaluationResult<long> GetValue(IntExpression expression, ProcessActionScopes state) => this.GetValue(expression, state, this.EvaluateScope);

    public EvaluationResult<long> GetValue(IntExpression expression, RecordDataValue state) => this.GetValue(expression, state, this.EvaluateState);

    public EvaluationResult<double> GetValue(NumberExpression expression, ProcessActionScopes state) => this.GetValue(expression, state, this.EvaluateScope);

    public EvaluationResult<double> GetValue(NumberExpression expression, RecordDataValue state) => this.GetValue(expression, state, this.EvaluateState);

    public EvaluationResult<TValue?> GetValue<TValue>(ObjectExpression<TValue> expression, RecordDataValue state) where TValue : BotElement
    {
        throw new NotImplementedException(); // %%% TODO: IMPLEMENT
    }

    public ImmutableArray<T> GetValue<T>(ArrayExpression<T> expression, RecordDataValue state)
    {
        throw new NotImplementedException(); // %%% TODO: IMPLEMENT
    }

    public ImmutableArray<T> GetValue<T>(ArrayExpressionOnly<T> expression, RecordDataValue state)
    {
        throw new NotImplementedException(); // %%% TODO: IMPLEMENT
    }

    public EvaluationResult<TValue> GetValue<TValue>(EnumExpression<TValue> expression, ProcessActionScopes state) where TValue : EnumWrapper =>
        this.GetValue<TValue, ProcessActionScopes>(expression, state, this.EvaluateScope);

    public EvaluationResult<TValue> GetValue<TValue>(EnumExpression<TValue> expression, RecordDataValue state) where TValue : EnumWrapper =>
        this.GetValue<TValue, RecordDataValue>(expression, state, this.EvaluateState);

    public DialogSchemaName GetValue(DialogExpression expression, RecordDataValue state)
    {
        throw new NotSupportedException();
    }

    public EvaluationResult<string> GetValue(AdaptiveCardExpression expression, RecordDataValue state)
    {
        throw new NotSupportedException();
    }

    public EvaluationResult<FileDataValue?> GetValue(FileExpression expression, RecordDataValue state)
    {
        throw new NotSupportedException();
    }

    private EvaluationResult<bool> GetValue<TState>(BoolExpression expression, TState state, Func<ExpressionBase, TState, FormulaValue> evaluator)
    {
        Throw.IfNull(expression, nameof(expression));

        if (expression.IsLiteral)
        {
            return new EvaluationResult<bool>(expression.LiteralValue, SensitivityLevel.None); // %%% SENSITIVITY ???
        }

        FormulaValue expressionValue = evaluator.Invoke(expression, state);

        if (expressionValue is BlankValue)
        {
            return new EvaluationResult<bool>(default, SensitivityLevel.None); // %%% SENSITIVITY ???
        }

        if (expressionValue is not BooleanValue formulaValue)
        {
            throw new InvalidExpressionOutputTypeException(expressionValue.GetDataType(), DataType.Boolean);
        }

        return new EvaluationResult<bool>(formulaValue.Value, SensitivityLevel.None); // %%% SENSITIVITY ???
    }

    private EvaluationResult<string> GetValue<TState>(StringExpression expression, TState state, Func<ExpressionBase, TState, FormulaValue> evaluator)
    {
        Throw.IfNull(expression, nameof(expression));

        if (expression.IsLiteral)
        {
            return new EvaluationResult<string>(expression.LiteralValue, SensitivityLevel.None); // %%% SENSITIVITY ???
        }

        FormulaValue expressionValue = evaluator.Invoke(expression, state);

        if (expressionValue is BlankValue)
        {
            return new EvaluationResult<string>(string.Empty, SensitivityLevel.None); // %%% SENSITIVITY ???
        }

        if (expressionValue is RecordValue recordValue)
        {
            return new EvaluationResult<string>(JsonSerializer.Serialize(recordValue, s_options), SensitivityLevel.None); // %%% SENSITIVITY ???
        }

        if (expressionValue is not StringValue formulaValue)
        {
            throw new InvalidExpressionOutputTypeException(expressionValue.GetDataType(), DataType.String);
        }

        return new EvaluationResult<string>(formulaValue.Value, SensitivityLevel.None); // %%% SENSITIVITY ???
    }

    private EvaluationResult<long> GetValue<TState>(IntExpression expression, TState state, Func<ExpressionBase, TState, FormulaValue> evaluator)
    {
        Throw.IfNull(expression, nameof(expression));

        if (expression.IsLiteral)
        {
            return new EvaluationResult<long>(expression.LiteralValue, SensitivityLevel.None); // %%% SENSITIVITY ???
        }

        FormulaValue expressionValue = evaluator.Invoke(expression, state);

        if (expressionValue is not PrimitiveValue<int> formulaValue) // %%% CORRECT ???
        {
            throw new InvalidExpressionOutputTypeException(expressionValue.GetDataType(), DataType.Number);
        }

        return new EvaluationResult<long>(formulaValue.Value, SensitivityLevel.None); // %%% SENSITIVITY ???
    }

    private EvaluationResult<double> GetValue<TState>(NumberExpression expression, TState state, Func<ExpressionBase, TState, FormulaValue> evaluator)
    {
        Throw.IfNull(expression, nameof(expression));

        if (expression.IsLiteral)
        {
            return new EvaluationResult<double>(expression.LiteralValue, SensitivityLevel.None); // %%% SENSITIVITY ???
        }

        FormulaValue expressionValue = evaluator.Invoke(expression, state);

        if (expressionValue is not NumberValue formulaValue)
        {
            throw new InvalidExpressionOutputTypeException(expressionValue.GetDataType(), DataType.Number);
        }

        return new EvaluationResult<double>(formulaValue.Value, SensitivityLevel.None); // %%% SENSITIVITY ???
    }

    private EvaluationResult<DataValue> GetValue<TState>(ValueExpression expression, TState state, Func<ExpressionBase, TState, FormulaValue> evaluator)
    {
        Throw.IfNull(expression, nameof(expression));

        if (expression.IsLiteral)
        {
            return new EvaluationResult<DataValue>(expression.LiteralValue ?? BlankDataValue.Instance, SensitivityLevel.None); // %%% SENSITIVITY ???
        }

        FormulaValue expressionValue = evaluator.Invoke(expression, state);

        return new EvaluationResult<DataValue>(expressionValue.GetDataValue(), SensitivityLevel.None); // %%% SENSITIVITY ???
    }

    private EvaluationResult<TValue> GetValue<TValue, TState>(EnumExpression<TValue> expression, TState state, Func<ExpressionBase, TState, FormulaValue> evaluator) where TValue : EnumWrapper
    {
        Throw.IfNull(expression, nameof(expression));

        if (expression.IsLiteral)
        {
            return new EvaluationResult<TValue>(expression.LiteralValue, SensitivityLevel.None); // %%% SENSITIVITY ???
        }

        FormulaValue expressionValue = evaluator.Invoke(expression, state);
        SensitivityLevel expressionSensitivity = SensitivityLevel.None; // %%% SENSITIVITY ???

        return expressionValue switch
        {
            BlankValue => new EvaluationResult<TValue>(EnumWrapper.Create<TValue>(0), expressionSensitivity),
            StringValue s when s.Value is not null => new EvaluationResult<TValue>(EnumWrapper.Create<TValue>(s.Value), expressionSensitivity),
            StringValue => new EvaluationResult<TValue>(EnumWrapper.Create<TValue>(0), expressionSensitivity),
            NumberValue number => new EvaluationResult<TValue>(EnumWrapper.Create<TValue>((int)number.Value), expressionSensitivity),
            //OptionDataValue option => new EvaluationResult<TValue>(EnumWrapper.Create<TValue>(option.Value.Value), expressionSensitivity),
            _ => throw new InvalidExpressionOutputTypeException(expressionValue.GetDataType(), DataType.String),
        };
    }

    private FormulaValue EvaluateState(ExpressionBase expression, RecordDataValue state)
    {
        foreach (KeyValuePair<string, DataValue> kvp in state.Properties)
        {
            if (kvp.Value is RecordDataValue scopeRecord)
            {
                this._engine.SetScope(kvp.Key, scopeRecord.ToRecordValue());
            }
        }

        return this.Evaluate(expression);
    }

    private FormulaValue EvaluateScope(ExpressionBase expression, ProcessActionScopes state)
    {
        this._engine.SetScope(ActionScopeType.System.Name, state.BuildRecord(ActionScopeType.System));
        this._engine.SetScope(ActionScopeType.Env.Name, state.BuildRecord(ActionScopeType.Env));
        this._engine.SetScope(ActionScopeType.Global.Name, state.BuildRecord(ActionScopeType.Global));
        this._engine.SetScope(ActionScopeType.Topic.Name, state.BuildRecord(ActionScopeType.Topic));

        return this.Evaluate(expression);
    }

    private FormulaValue Evaluate(ExpressionBase expression)
    {
        string? expressionText =
            expression.IsVariableReference ?
            expression.VariableReference?.Format() :
            expression.ExpressionText;

        return this._engine.Eval(expressionText);
    }
}

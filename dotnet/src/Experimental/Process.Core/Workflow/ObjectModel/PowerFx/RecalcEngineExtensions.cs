// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx;
using Microsoft.PowerFx.Types;

namespace Microsoft.SemanticKernel.Process.Workflows.PowerFx;

internal static class RecalcEngineExtensions
{
    public static void SetScopedVariable(this RecalcEngine engine, ProcessActionScopes scopes, ActionScopeType scope, string varName, FormulaValue value)
    {
        // Validate inputs and assign value.
        scopes.Set(varName, scope, value);

        // Rebuild scope record and update engine
        RecordValue scopeRecord = scopes.BuildRecord(scope);
        engine.DeleteFormula(scope.Name);
        engine.UpdateVariable(scope.Name, scopeRecord);
    }

    public static FormulaValue EvaluateExpression(this RecalcEngine engine, ValueExpression? value)
    {
        if (value is null)
        {
            return BlankValue.NewBlank();
        }

        if (value.IsVariableReference)
        {
            return engine.Eval(value.VariableReference?.Format());
        }

        if (value.IsExpression)
        {
            return engine.Eval(value.ExpressionText);
        }

        if (value.IsLiteral)
        {
            return value.LiteralValue.ToFormulaValue();
        }

        // %%% TODO: value.StructuredRecordExpression ???

        return BlankValue.NewBlank();
    }
}

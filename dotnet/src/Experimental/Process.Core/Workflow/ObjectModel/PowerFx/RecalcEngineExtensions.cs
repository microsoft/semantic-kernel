// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows.Extensions;

namespace Microsoft.SemanticKernel.Process.Workflows.PowerFx;

internal static class RecalcEngineExtensions
{
    public static void ClearScopedVariable(this RecalcEngine engine, ProcessActionScopes scopes, ActionScopeType scope, string varName)
    {
        // Validate inputs and assign value.
        scopes.Remove(varName, scope); // %%% CONSIDER: SET TO BLANK ???

        // Rebuild scope record and update engine
        RecordValue scopeRecord = scopes.BuildRecord(scope);
        engine.DeleteFormula(scope.Name);
        engine.UpdateVariable(scope.Name, scopeRecord);
    }

    public static void SetScopedVariable(this RecalcEngine engine, ProcessActionScopes scopes, ActionScopeType scope, string varName, FormulaValue value)
    {
        // Validate inputs and assign value.
        scopes.Set(varName, scope, value);

        // Rebuild scope record and update engine
        RecordValue scopeRecord = scopes.BuildRecord(scope);
        engine.DeleteFormula(scope.Name);
        engine.UpdateVariable(scope.Name, scopeRecord);
    }

    public static FormulaValue EvaluateExpression(this RecalcEngine engine, ExpressionBase? value)
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
            return value.GetLiteralValue().ToFormulaValue();
        }

        // %%% TODO: value.StructuredRecordExpression ???

        return BlankValue.NewBlank();
    }
}

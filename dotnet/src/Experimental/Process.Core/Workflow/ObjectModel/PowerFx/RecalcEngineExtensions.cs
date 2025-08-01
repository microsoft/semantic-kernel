// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows.Extensions;

namespace Microsoft.SemanticKernel.Process.Workflows.PowerFx;

internal static class RecalcEngineExtensions
{
    public static void ClearScope(this RecalcEngine engine, ProcessActionScopes scopes, ActionScopeType scope)
    {
        // Clear all scope values.
        scopes.Clear(scope);

        // Rebuild scope record and update engine
        UpdateScope(engine, scopes, scope);
    }

    public static void ClearScopedVariable(this RecalcEngine engine, ProcessActionScopes scopes, PropertyPath variablePath) =>
        engine.ClearScopedVariable(scopes, ActionScopeType.Parse(variablePath.VariableScopeName), Throw.IfNull(variablePath.VariableName));

    public static void ClearScopedVariable(this RecalcEngine engine, ProcessActionScopes scopes, ActionScopeType scope, string varName)
    {
        // Clear value.
        scopes.Remove(varName, scope);

        // Rebuild scope record and update engine
        UpdateScope(engine, scopes, scope);
    }

    public static void SetScopedVariable(this RecalcEngine engine, ProcessActionScopes scopes, PropertyPath variablePath, FormulaValue value) =>
        engine.SetScopedVariable(scopes, ActionScopeType.Parse(variablePath.VariableScopeName), Throw.IfNull(variablePath.VariableName), value);

    public static void SetScopedVariable(this RecalcEngine engine, ProcessActionScopes scopes, ActionScopeType scope, string varName, FormulaValue value)
    {
        // Assign value.
        scopes.Set(varName, scope, value);

        // Rebuild scope record and update engine
        UpdateScope(engine, scopes, scope);
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
            return value.GetLiteralValue().ToFormulaValue(); // %%% GetLiteralValue
        }

        // %%% TODO: value.StructuredRecordExpression ???
        // %%% TODO: ArrayExpression

        return BlankValue.NewBlank();
    }

    private static void UpdateScope(RecalcEngine engine, ProcessActionScopes scopes, ActionScopeType scope)
    {
        RecordValue scopeRecord = scopes.BuildRecord(scope);
        engine.DeleteFormula(scope.Name);
        engine.UpdateVariable(scope.Name, scopeRecord);
    }
}

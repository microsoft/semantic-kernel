// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx;
using Microsoft.PowerFx.Types;

namespace Microsoft.SemanticKernel.Process.Workflows.PowerFx;

internal static class RecalcEngineExtensions
{
    public static void ClearScope(this RecalcEngine engine, ProcessActionScopes scopes, ActionScopeType scope)
    {
        // Clear all scope values.
        scopes.Clear(scope);

        // Rebuild scope record and update engine
        engine.UpdateScope(scopes, scope);
    }

    public static void ClearScopedVariable(this RecalcEngine engine, ProcessActionScopes scopes, PropertyPath variablePath) =>
        engine.ClearScopedVariable(scopes, ActionScopeType.Parse(variablePath.VariableScopeName), Throw.IfNull(variablePath.VariableName));

    public static void ClearScopedVariable(this RecalcEngine engine, ProcessActionScopes scopes, ActionScopeType scope, string varName)
    {
        // Clear value.
        scopes.Remove(varName, scope);

        // Rebuild scope record and update engine
        engine.UpdateScope(scopes, scope);
    }

    public static void SetScopedVariable(this RecalcEngine engine, ProcessActionScopes scopes, PropertyPath variablePath, FormulaValue value) =>
        engine.SetScopedVariable(scopes, ActionScopeType.Parse(variablePath.VariableScopeName), Throw.IfNull(variablePath.VariableName), value);

    public static void SetScopedVariable(this RecalcEngine engine, ProcessActionScopes scopes, ActionScopeType scope, string varName, FormulaValue value)
    {
        // Assign value.
        scopes.Set(varName, scope, value);

        // Rebuild scope record and update engine
        engine.UpdateScope(scopes, scope);
    }

    public static void SetScope(this RecalcEngine engine, string scopeName, RecordValue scopeRecord)
    {
        engine.DeleteFormula(scopeName);
        engine.UpdateVariable(scopeName, scopeRecord);
    }

    private static void UpdateScope(this RecalcEngine engine, ProcessActionScopes scopes, ActionScopeType scope)
    {
        RecordValue scopeRecord = scopes.BuildRecord(scope);
        engine.SetScope(scope.Name, scopeRecord);
    }
}

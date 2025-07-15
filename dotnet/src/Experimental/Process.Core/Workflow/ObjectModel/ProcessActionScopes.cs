// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.PowerFx.Types;

namespace Microsoft.SemanticKernel.Process.Workflows;

internal static class ActionScopeTypes
{
    public const string Topic = nameof(Topic);
    public const string Global = nameof(Global);
    public const string System = nameof(System);
}

internal sealed class ProcessActionScope : Dictionary<string, FormulaValue>;

internal sealed class ProcessActionScopes : Dictionary<string, ProcessActionScope>
{
    public ProcessActionScopes()
    {
        this[ActionScopeTypes.Topic] = [];
        this[ActionScopeTypes.Global] = [];
        this[ActionScopeTypes.System] = [];
    }
}

internal static class ProcessActionScopeExtensions
{
    public static RecordValue BuildRecord(this ProcessActionScope scope)
    {
        return FormulaValue.NewRecordFromFields(GetFields());

        IEnumerable<NamedValue> GetFields()
        {
            foreach (KeyValuePair<string, FormulaValue> kvp in scope)
            {
                yield return new NamedValue(kvp.Key, kvp.Value);
            }
        }
    }

    public static ProcessActionScope AssignValue(this ProcessActionScopes scopes, string scopeName, string varName, FormulaValue value)
    {
        if (!scopes.TryGetValue(scopeName, out ProcessActionScope? scope))
        {
            throw new InvalidActionException("Unknown scope: " + scopeName);
        }

        scope[varName] = value;

        return scope;
    }
}

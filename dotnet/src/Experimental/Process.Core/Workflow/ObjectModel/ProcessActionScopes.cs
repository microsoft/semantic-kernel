// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows.Extensions;

namespace Microsoft.SemanticKernel.Process.Workflows;

/// <summary>
/// Describes the type of action scope.
/// </summary>
internal sealed class ActionScopeType // %%% NEEDED
{
    // https://msazure.visualstudio.com/CCI/_git/ObjectModel?path=/src/ObjectModel/Nodes/VariableScopeNames.cs&_a=contents&version=GBmain
    public static readonly ActionScopeType Env = new(VariableScopeNames.Environment);
    public static readonly ActionScopeType Topic = new(VariableScopeNames.Topic);
    public static readonly ActionScopeType Global = new(VariableScopeNames.Global);
    public static readonly ActionScopeType System = new(VariableScopeNames.System);

    public static ActionScopeType Parse(string? scope)
    {
        return scope switch
        {
            nameof(Env) => Env,
            nameof(Global) => Global,
            nameof(System) => System,
            nameof(Topic) => Topic,
            null => throw new InvalidScopeException("Undefined action scope type."),
            _ => throw new InvalidScopeException($"Unknown action scope type: {scope}."),
        };
    }

    private ActionScopeType(string name)
    {
        this.Name = name;
    }

    public string Name { get; }

    public string Format(string name) => $"{this.Name}.{name}";

    public override string ToString() => this.Name;

    public override int GetHashCode() => this.Name.GetHashCode();

    public override bool Equals(object? obj) =>
        (obj is ActionScopeType other && this.Name.Equals(other.Name, StringComparison.Ordinal)) ||
        (obj is string name && this.Name.Equals(name, StringComparison.Ordinal));
}

/// <summary>
/// The set of variables for a specific action scope.
/// </summary>
internal sealed class ProcessActionScope : Dictionary<string, FormulaValue>
{
    public RecordValue BuildRecord()
    {
        return FormulaValue.NewRecordFromFields(GetFields());

        IEnumerable<NamedValue> GetFields()
        {
            foreach (KeyValuePair<string, FormulaValue> kvp in this)
            {
                yield return new NamedValue(kvp.Key, kvp.Value);
            }
        }
    }

    public RecordDataValue BuildState()
    {
        RecordDataValue.Builder recordBuilder = new();

        foreach (KeyValuePair<string, FormulaValue> kvp in this)
        {
            recordBuilder.Properties.Add(kvp.Key, kvp.Value.GetDataValue());
        }

        return recordBuilder.Build();
    }
}

/// <summary>
/// Contains all action scopes for a process.
/// </summary>
internal sealed class ProcessActionScopes
{
    private readonly ImmutableDictionary<ActionScopeType, ProcessActionScope> _scopes;

    public ProcessActionScopes()
    {
        Dictionary<ActionScopeType, ProcessActionScope> scopes =
            new()
            {
                { ActionScopeType.Env, [] },
                { ActionScopeType.Topic, [] },
                { ActionScopeType.Global, [] },
                { ActionScopeType.System, [] },
            };

        this._scopes = scopes.ToImmutableDictionary();
    }

    public RecordValue BuildRecord(ActionScopeType scope) => this._scopes[scope].BuildRecord();

    public RecordDataValue BuildState()
    {
        return RecordDataValue.RecordFromFields(BuildStateFields());

        IEnumerable<KeyValuePair<string, DataValue>> BuildStateFields()
        {
            foreach (KeyValuePair<ActionScopeType, ProcessActionScope> kvp in this._scopes)
            {
                yield return new(kvp.Key.Name, kvp.Value.BuildState());
            }
        }
    }

    public FormulaValue Get(string name, ActionScopeType? type = null)
    {
        if (this._scopes[type ?? ActionScopeType.Topic].TryGetValue(name, out FormulaValue? value))
        {
            return value;
        }

        return FormulaValue.NewBlank();
    }

    public void Clear(ActionScopeType type) => this._scopes[type].Clear();

    public void Remove(string name) => this.Remove(name, ActionScopeType.Topic);

    public void Remove(string name, ActionScopeType type) => this._scopes[type].Remove(name);

    public void Set(string name, FormulaValue value) => this.Set(name, ActionScopeType.Topic, value);

    public void Set(string name, ActionScopeType type, FormulaValue value) => this._scopes[type][name] = value;
}

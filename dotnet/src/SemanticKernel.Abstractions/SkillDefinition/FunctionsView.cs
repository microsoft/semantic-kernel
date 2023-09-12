// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Linq;
using System.Reflection;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Class used to copy and export data from the skill collection.
/// The data is mutable, but changes do not affect the skill collection.
/// The class can be used to create custom lists in case your scenario needs to.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
public sealed class FunctionsView
{
    private object _lock = new();
    /// <summary>
    /// Collection of semantic skill names and function names, including function parameters.
    /// Functions are grouped by skill name.
    /// </summary>
    public IReadOnlyDictionary<string, IReadOnlyCollection<FunctionView>> SemanticFunctions => this.GetFunctions(nativeFunctionCheck: false);

    /// <summary>
    /// Collection of native skill names and function views, including function parameters.
    /// Functions are grouped by skill name.
    /// </summary>
    public IReadOnlyDictionary<string, IReadOnlyCollection<FunctionView>> NativeFunctions => this.GetFunctions(nativeFunctionCheck: true);

    private readonly ConcurrentDictionary<string, List<FunctionView>> _semanticFunctions = new(StringComparer.OrdinalIgnoreCase);
    private readonly ConcurrentDictionary<string, List<FunctionView>> _nativeFunctions = new(StringComparer.OrdinalIgnoreCase);

    /// <summary>
    /// Add a function to the list
    /// </summary>
    /// <param name="view">Function details</param>
    /// <returns>Current instance</returns>
    public FunctionsView AddFunction(FunctionView view)
    {
        lock (this._lock)
        {
            if (view.IsSemantic)
            {
                this._semanticFunctions.GetOrAdd(view.SkillName, _ => new()).Add(view);
            }
            else
            {
                this._nativeFunctions.GetOrAdd(view.SkillName, _ => new()).Add(view);
            }
        }

        return this;
    }

    /// <summary>
    /// Returns true if the function specified is unique and semantic
    /// </summary>
    /// <param name="skillName">Skill name</param>
    /// <param name="functionName">Function name</param>
    /// <returns>True if unique and semantic</returns>
    /// <exception cref="AmbiguousMatchException"></exception>
    public bool IsSemantic(string skillName, string functionName)
    {
        return this.IsFunctionCheck(skillName, functionName, nativeFunctionCheck: false);
    }

    /// <summary>
    /// Returns true if the function specified is unique and native
    /// </summary>
    /// <param name="skillName">Skill name</param>
    /// <param name="functionName">Function name</param>
    /// <returns>True if unique and native</returns>
    /// <exception cref="AmbiguousMatchException"></exception>
    public bool IsNative(string skillName, string functionName)
    {
        return this.IsFunctionCheck(skillName, functionName, nativeFunctionCheck: true);
    }

#pragma warning disable CA1859 // Use concrete types when possible for improved performance
    private IReadOnlyDictionary<string, IReadOnlyCollection<FunctionView>> GetFunctions(bool nativeFunctionCheck)
#pragma warning restore CA1859 // Use concrete types when possible for improved performance
    {
        ConcurrentDictionary<string, List<FunctionView>> targetFunctionDictionary = (nativeFunctionCheck)
            ? this._nativeFunctions
            : this._semanticFunctions;

        return new ReadOnlyFunctionsView(targetFunctionDictionary);
    }

    private class ReadOnlyFunctionsView : IReadOnlyDictionary<string, IReadOnlyCollection<FunctionView>>
    {
        private readonly ConcurrentDictionary<string, List<FunctionView>> _decorated;

        public IEnumerable<string> Keys => this._decorated.Keys;

        public IEnumerable<IReadOnlyCollection<FunctionView>> Values => this.GetValues();

        public int Count => this._decorated.Count;

        public IReadOnlyCollection<FunctionView> this[string key] => this._decorated[key].ToArray();

        public ReadOnlyFunctionsView(ConcurrentDictionary<string, List<FunctionView>> decorated)
        {
            this._decorated = decorated;
        }

        public bool TryGetValue(string key, out IReadOnlyCollection<FunctionView> value)
        {
            bool result = this._decorated.TryGetValue(key, out List<FunctionView>? decoratorValue);
#pragma warning disable CS8601 // Possible null reference assignment.
            value = decoratorValue?.ToArray();
#pragma warning restore CS8601 // Possible null reference assignment.

            return result;
        }

        public IEnumerator<KeyValuePair<string, IReadOnlyCollection<FunctionView>>> GetEnumerator()
        {
            return new ReadOnlyFunctionsViewEnumerator(this._decorated.GetEnumerator());
        }

        IEnumerator IEnumerable.GetEnumerator()
        {
            return new ReadOnlyFunctionsViewEnumerator(this._decorated.GetEnumerator());
        }

        public bool ContainsKey(string key)
        {
            return this._decorated.ContainsKey(key);
        }

        private IEnumerable<IReadOnlyCollection<FunctionView>> GetValues()
        {
            foreach (var decoratorValue in this._decorated.Values)
            {
                yield return decoratorValue.ToArray();
            }
        }
    }

    private class ReadOnlyFunctionsViewEnumerator : IEnumerator<KeyValuePair<string, IReadOnlyCollection<FunctionView>>>
    {
        private readonly IEnumerator<KeyValuePair<string, List<FunctionView>>> _decorated;

        public ReadOnlyFunctionsViewEnumerator(IEnumerator<KeyValuePair<string, List<FunctionView>>> decorated)
        {
            this._decorated = decorated;
        }

        public KeyValuePair<string, IReadOnlyCollection<FunctionView>> Current => new(this._decorated.Current.Key, this._decorated.Current.Value.ToArray());

        object IEnumerator.Current => this.Current;

        public void Dispose()
        {
            this._decorated.Dispose();
        }

        public bool MoveNext()
        {
            return this._decorated.MoveNext();
        }

        public void Reset()
        {
            this._decorated.Reset();
        }
    }

    private bool IsFunctionCheck(string skillName, string functionName, bool nativeFunctionCheck)
    {
        this._semanticFunctions.TryGetValue(skillName, out var semanticFunctions);
        var foundSemanticFunction = semanticFunctions?.Any(x => string.Equals(x.Name, functionName, StringComparison.OrdinalIgnoreCase))
                                    ?? false;

        this._nativeFunctions.TryGetValue(skillName, out var nativeFunctions);
        var foundNativeFunction = nativeFunctions?.Any(x => string.Equals(x.Name, functionName, StringComparison.OrdinalIgnoreCase))
                                  ?? false;

        if (foundSemanticFunction && foundNativeFunction)
        {
            throw new AmbiguousMatchException("There are 2 functions with the same name, one native and one semantic");
        }

        return (nativeFunctionCheck)
            ? foundNativeFunction
            : foundSemanticFunction;
    }

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay => $"Native = {this._nativeFunctions.Count}, Semantic = {this._semanticFunctions.Count}";
}

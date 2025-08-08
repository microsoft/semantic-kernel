// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Process.Workflows;

internal delegate void ScopeCompletionAction(string scopeId); // %%% NEEDED: scopeId ???

internal sealed class ProcessActionStack
{
    private readonly Stack<string> _actionStack = [];
    private readonly Dictionary<string, ScopeCompletionAction?> _actionScopes = [];

    public string CurrentScope =>
        this._actionStack.Count > 0 ?
        this._actionStack.Peek() :
        throw new InvalidOperationException("No scope defined"); // %%% EXCEPTION TYPE

    public void Recognize(string scopeId, ScopeCompletionAction? callback = null)
    {
#if NET
        if (this._actionScopes.TryAdd(scopeId, callback))
        {
#else
        if (!this._actionScopes.ContainsKey(scopeId))
        {
            this._actionScopes[scopeId] = callback;
#endif
            // If the scope is new, push it onto the stack
            this._actionStack.Push(scopeId);
        }
        else
        {
            // Otherwise, unwind the stack to the given scope
            string currentScopeId;
            while ((currentScopeId = this.CurrentScope) != scopeId)
            {
                ScopeCompletionAction? unwoundCallback = this._actionScopes[currentScopeId];
                unwoundCallback?.Invoke(currentScopeId);
                this._actionStack.Pop();
                this._actionScopes.Remove(currentScopeId);
            }
        }
    }
}

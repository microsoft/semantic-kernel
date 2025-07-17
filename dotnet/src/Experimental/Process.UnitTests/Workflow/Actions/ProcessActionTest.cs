// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows;
using Microsoft.SemanticKernel.Process.Workflows.PowerFx;
using Xunit;
using Xunit.Abstractions;

namespace Microsoft.SemanticKernel.Process.UnitTests.Workflows.Actions;

/// <summary>
/// Base test class for <see cref="ProcessAction"/> implementations.
/// </summary>
public abstract class ProcessActionTest(ITestOutputHelper output) : WorkflowTest(output)
{
    internal ProcessActionScopes Scopes { get; } = new();

    protected ActionId CreateActionId() => new($"{this.GetType().Name}_{Guid.NewGuid():N}");

    protected string FormatDisplayName(string name) => $"{this.GetType().Name}_{name}";

    internal Task ExecuteAction(ProcessAction action, Kernel? kernel = null) =>
        action.ExecuteAsync(
            new ProcessActionContext(
                RecalcEngineFactory.Create(this.Scopes, 5000),
                this.Scopes,
                kernel ?? new Kernel()),
            cancellationToken: default);

    internal void VerifyModel(DialogAction model, ProcessAction action)
    {
        Assert.Equal(model.Id, action.Id);
        Assert.Equal(model, action.Model);
    }

    protected void VerifyState(string variableName, FormulaValue expectedValue) => this.VerifyState(variableName, ActionScopeType.Topic, expectedValue);

    internal void VerifyState(string variableName, ActionScopeType scope, FormulaValue expectedValue)
    {
        FormulaValue actualValue = this.Scopes.Get(variableName, scope);
        Assert.Equivalent(expectedValue, actualValue);
    }

    protected void VerifyUndefined(string variableName) => this.VerifyUndefined(variableName, ActionScopeType.Topic);

    internal void VerifyUndefined(string variableName, ActionScopeType scope)
    {
        Assert.Throws<KeyNotFoundException>(() => this.Scopes.Get(variableName, scope));
    }
}

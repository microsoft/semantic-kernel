// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows.Actions;
using Xunit;
using Xunit.Abstractions;

namespace Microsoft.SemanticKernel.Process.UnitTests.Workflows.Actions;

/// <summary>
/// Tests for <see cref="ClearAllVariablesAction"/>.
/// </summary>
public sealed class ClearAllVariablesActionTest(ITestOutputHelper output) : ProcessActionTest(output)
{
    [Fact]
    public async Task ClearUserScope()
    {
        // Arrange
        this.Scopes.Set("NoVar", FormulaValue.New("Old value"));

        ClearAllVariables model =
            this.CreateModel(
                this.FormatDisplayName(nameof(ClearUserScope)),
                VariablesToClear.UserScopedVariables);

        // Act
        ClearAllVariablesAction action = new(model);
        await this.ExecuteAction(action);

        // Assert
        this.VerifyModel(model, action);
        this.VerifyUndefined("NoVar");
    }

    [Fact]
    public async Task ClearUndefinedScope()
    {
        // Arrange
        ClearAllVariables model =
            this.CreateModel(
                this.FormatDisplayName(nameof(ClearUndefinedScope)),
                VariablesToClear.UserScopedVariables);

        // Act
        ClearAllVariablesAction action = new(model);
        await this.ExecuteAction(action);

        // Assert
        this.VerifyModel(model, action);
        this.VerifyUndefined("NoVar");
    }

    private ClearAllVariables CreateModel(string displayName, VariablesToClear variableTarget)
    {
        ClearAllVariables.Builder actionBuilder =
            new()
            {
                Id = this.CreateActionId(),
                DisplayName = this.FormatDisplayName(displayName),
                Variables = EnumExpression<VariablesToClearWrapper>.Literal(VariablesToClearWrapper.Get(variableTarget)),
            };

        ClearAllVariables model = this.AssignParent<ClearAllVariables>(actionBuilder);

        return model;
    }
}

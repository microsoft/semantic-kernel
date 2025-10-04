// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows.Actions;
using Xunit;
using Xunit.Abstractions;

namespace Microsoft.SemanticKernel.Process.UnitTests.Workflows.Actions;

/// <summary>
/// Tests for <see cref="ResetVariableAction"/>.
/// </summary>
public sealed class ResetVariableTest(ITestOutputHelper output) : ProcessActionTest(output)
{
    [Fact]
    public async Task ResetDefinedValue()
    {
        // Arrange
        this.Scopes.Set("MyVar", FormulaValue.New("Old value"));

        ResetVariable model =
            this.CreateModel(
                this.FormatDisplayName(nameof(ResetDefinedValue)),
                FormatVariablePath("MyVar"));

        // Act
        ResetVariableAction action = new(model);
        await this.ExecuteAction(action);

        // Assert
        this.VerifyModel(model, action);
        this.VerifyUndefined("MyVar");
    }

    [Fact]
    public async Task ResetUndefinedValue()
    {
        // Arrange
        ResetVariable model =
            this.CreateModel(
                this.FormatDisplayName(nameof(ResetUndefinedValue)),
                FormatVariablePath("NoVar"));

        // Act
        ResetVariableAction action = new(model);
        await this.ExecuteAction(action);

        // Assert
        this.VerifyModel(model, action);
        this.VerifyUndefined("NoVar");
    }

    private ResetVariable CreateModel(string displayName, string variablePath)
    {
        ResetVariable.Builder actionBuilder =
            new()
            {
                Id = this.CreateActionId(),
                DisplayName = this.FormatDisplayName(displayName),
                Variable = InitializablePropertyPath.Create(variablePath),
            };

        ResetVariable model = this.AssignParent<ResetVariable>(actionBuilder);

        return model;
    }
}

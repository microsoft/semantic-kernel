// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows.Actions;
using Xunit;
using Xunit.Abstractions;

namespace Microsoft.SemanticKernel.Process.UnitTests.Workflows.Actions;

/// <summary>
/// Tests for <see cref="SetTextVariableAction"/>.
/// </summary>
public sealed class SetTextVariableActionTest(ITestOutputHelper output) : ProcessActionTest(output)
{
    [Fact]
    public async Task SetLiteralValue()
    {
        // Arrange
        SetTextVariable model =
            this.CreateModel(
                this.FormatDisplayName(nameof(SetLiteralValue)),
                FormatVariablePath("TextVar"),
                "Text variable value");

        // Act
        SetTextVariableAction action = new(model);
        await this.ExecuteAction(action);

        // Assert
        this.VerifyModel(model, action);
        this.VerifyState("TextVar", FormulaValue.New("Text variable value"));
    }

    [Fact]
    public async Task UpdateExistingValue()
    {
        // Arrange
        this.Scopes.Set("TextVar", FormulaValue.New("Old value"));

        SetTextVariable model =
            this.CreateModel(
                this.FormatDisplayName(nameof(UpdateExistingValue)),
                FormatVariablePath("TextVar"),
                "New value");

        // Act
        SetTextVariableAction action = new(model);
        await this.ExecuteAction(action);

        // Assert
        this.VerifyModel(model, action);
        this.VerifyState("TextVar", FormulaValue.New("New value"));
    }

    private SetTextVariable CreateModel(string displayName, string variablePath, string textValue)
    {
        SetTextVariable.Builder actionBuilder =
            new()
            {
                Id = this.CreateActionId(),
                DisplayName = this.FormatDisplayName(displayName),
                Variable = InitializablePropertyPath.Create(variablePath),
                Value = TemplateLine.Parse(textValue),
            };

        SetTextVariable model = this.AssignParent<SetTextVariable>(actionBuilder);

        return model;
    }
}

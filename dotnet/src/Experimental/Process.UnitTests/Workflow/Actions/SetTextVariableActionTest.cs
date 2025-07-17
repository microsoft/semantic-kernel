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
    public async Task CaptureActivity()
    {
        // Arrange
        SetTextVariable model =
            this.CreateModel(
                this.FormatDisplayName(nameof(CaptureActivity)),
                FormatVariablePath("TextVar"),
                "Text variable value");

        // Act
        SetTextVariableAction action = new(model);
        await this.ExecuteAction(action);

        // Assert
        this.VerifyModel(model, action);
        this.VerifyState("TextVar", FormulaValue.New("Text variable value"));
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

        SetTextVariable model = actionBuilder.Build();

        return model;
    }
}

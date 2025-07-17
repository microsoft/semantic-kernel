// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows;
using Microsoft.SemanticKernel.Process.Workflows.Actions;
using Xunit;
using Xunit.Abstractions;

namespace Microsoft.SemanticKernel.Process.UnitTests.Workflows.Actions;

/// <summary>
/// Tests for <see cref="SetVariableAction"/>.
/// </summary>
public sealed class SetVariableActionTest(ITestOutputHelper output) : ProcessActionTest(output)
{
    [Fact]
    public void InvalidModel()
    {
        // Arrange, Act, Assert
        Assert.Throws<InvalidActionException>(() => new SetVariableAction(new SetVariable()));
    }

    [Fact]
    public async Task SetNumericValue()
    {
        // Arrange, Act, Assert
        await this.ExecuteTest(
            displayName: nameof(SetNumericValue),
            variableName: "TestVariable",
            variableValue: new NumberDataValue(42),
            expectedValue: FormulaValue.New(42));
    }

    [Fact]
    public async Task SetStringValue()
    {
        // Arrange, Act, Assert
        await this.ExecuteTest(
            displayName: nameof(SetStringValue),
            variableName: "TestVariable",
            variableValue: new StringDataValue("Text"),
            expectedValue: FormulaValue.New("Text"));
    }

    [Fact]
    public async Task SetBooleanValue()
    {
        // Arrange, Act, Assert
        await this.ExecuteTest(
            displayName: nameof(SetBooleanValue),
            variableName: "TestVariable",
            variableValue: new BooleanDataValue(true),
            expectedValue: FormulaValue.New(true));
    }

    [Fact]
    public async Task SetBooleanExpression()
    {
        // Arrange
        ValueExpression.Builder expressionBuilder = new(ValueExpression.Expression("true || false"));

        // Act, Assert
        await this.ExecuteTest(
            displayName: nameof(SetBooleanExpression),
            variableName: "TestVariable",
            valueExpression: expressionBuilder,
            expectedValue: FormulaValue.New(true));
    }

    [Fact]
    public async Task SetNumberExpression()
    {
        // Arrange
        ValueExpression.Builder expressionBuilder = new(ValueExpression.Expression("9 - 3"));

        // Act, Assert
        await this.ExecuteTest(
            displayName: nameof(SetBooleanExpression),
            variableName: "TestVariable",
            valueExpression: expressionBuilder,
            expectedValue: FormulaValue.New(6));
    }

    [Fact]
    public async Task SetStringExpression()
    {
        // Arrange
        ValueExpression.Builder expressionBuilder = new(ValueExpression.Expression(@"Concatenate(""A"", ""B"", ""C"")"));

        // Act, Assert
        await this.ExecuteTest(
            displayName: nameof(SetBooleanExpression),
            variableName: "TestVariable",
            valueExpression: expressionBuilder,
            expectedValue: FormulaValue.New("ABC"));
    }

    [Fact]
    public async Task SetBooleanVariable()
    {
        // Arrange
        this.Scopes.Set("Source", FormulaValue.New(true));
        ValueExpression.Builder expressionBuilder = new(ValueExpression.Variable(PropertyPath.TopicVariable("Source")));

        // Act, Assert
        await this.ExecuteTest(
            displayName: nameof(SetBooleanExpression),
            variableName: "TestVariable",
            valueExpression: expressionBuilder,
            expectedValue: FormulaValue.New(true));
    }

    [Fact]
    public async Task SetNumberVariable()
    {
        // Arrange
        this.Scopes.Set("Source", FormulaValue.New(321));
        ValueExpression.Builder expressionBuilder = new(ValueExpression.Variable(PropertyPath.TopicVariable("Source")));

        // Act, Assert
        await this.ExecuteTest(
            displayName: nameof(SetBooleanExpression),
            variableName: "TestVariable",
            valueExpression: expressionBuilder,
            expectedValue: FormulaValue.New(321));
    }

    [Fact]
    public async Task SetStringVariable()
    {
        // Arrange
        this.Scopes.Set("Source", FormulaValue.New("Test"));
        ValueExpression.Builder expressionBuilder = new(ValueExpression.Variable(PropertyPath.TopicVariable("Source")));

        // Act, Assert
        await this.ExecuteTest(
            displayName: nameof(SetBooleanExpression),
            variableName: "TestVariable",
            valueExpression: expressionBuilder,
            expectedValue: FormulaValue.New("Test"));
    }

    [Fact]
    public async Task UpdateExistingValue()
    {
        // Arrange
        this.Scopes.Set("VarA", FormulaValue.New(33));

        // Act, Assert
        await this.ExecuteTest(
            displayName: nameof(UpdateExistingValue),
            variableName: "VarA",
            variableValue: new NumberDataValue(42),
            expectedValue: FormulaValue.New(42));
    }

    private Task ExecuteTest(
        string displayName,
        string variableName,
        DataValue variableValue,
        FormulaValue expectedValue)
    {
        // Arrange
        ValueExpression.Builder expressionBuilder = new(ValueExpression.Literal(variableValue));

        // Act & Assert
        return this.ExecuteTest(displayName, variableName, expressionBuilder, expectedValue);
    }

    private async Task ExecuteTest(
        string displayName,
        string variableName,
        ValueExpression.Builder valueExpression,
        FormulaValue expectedValue)
    {
        // Arrange
        SetVariable model =
            this.CreateModel(
                displayName,
                FormatVariablePath(variableName),
                valueExpression);

        this.Scopes.Set(variableName, FormulaValue.New(33));

        // Act
        SetVariableAction action = new(model);
        await this.ExecuteAction(action);

        // Assert
        this.VerifyModel(model, action);
        this.VerifyState(variableName, expectedValue);
    }

    private SetVariable CreateModel(string displayName, string variablePath, ValueExpression.Builder valueExpression)
    {
        SetVariable.Builder actionBuilder =
            new()
            {
                Id = this.CreateActionId(),
                DisplayName = this.FormatDisplayName(displayName),
                Variable = InitializablePropertyPath.Create(variablePath),
                Value = valueExpression,
            };

        SetVariable model = actionBuilder.Build();

        return model;
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows;
using Xunit;

namespace Microsoft.SemanticKernel.Process.UnitTests.Workflows;

public class ProcessActionScopesTests
{
    [Fact]
    public void ConstructorInitializesAllScopes()
    {
        // Arrange & Act
        ProcessActionScopes scopes = new();

        // Assert
        RecordValue envRecord = scopes.BuildRecord(ActionScopeType.Env);
        RecordValue topicRecord = scopes.BuildRecord(ActionScopeType.Topic);
        RecordValue globalRecord = scopes.BuildRecord(ActionScopeType.Global);
        RecordValue systemRecord = scopes.BuildRecord(ActionScopeType.System);

        Assert.NotNull(envRecord);
        Assert.NotNull(topicRecord);
        Assert.NotNull(globalRecord);
        Assert.NotNull(systemRecord);
    }

    [Fact]
    public void BuildRecordWhenEmpty()
    {
        // Arrange
        ProcessActionScopes scopes = new();

        // Act
        RecordValue record = scopes.BuildRecord(ActionScopeType.Topic);

        // Assert
        Assert.NotNull(record);
        Assert.Empty(record.Fields);
    }

    [Fact]
    public void BuildRecordContainsSetValues()
    {
        // Arrange
        ProcessActionScopes scopes = new();
        FormulaValue testValue = FormulaValue.New("test");
        scopes.Set("key1", ActionScopeType.Topic, testValue);

        // Act
        RecordValue record = scopes.BuildRecord(ActionScopeType.Topic);

        // Assert
        Assert.NotNull(record);
        Assert.Single(record.Fields);
        Assert.Equal("key1", record.Fields.First().Name);
        Assert.Equal(testValue, record.Fields.First().Value);
    }

    [Fact]
    public void BuildRecordForAllScopeTypes()
    {
        // Arrange
        ProcessActionScopes scopes = new();
        FormulaValue testValue = FormulaValue.New("test");

        // Act & Assert
        scopes.Set("envKey", ActionScopeType.Env, testValue);
        RecordValue envRecord = scopes.BuildRecord(ActionScopeType.Env);
        Assert.Single(envRecord.Fields);

        scopes.Set("topicKey", ActionScopeType.Topic, testValue);
        RecordValue topicRecord = scopes.BuildRecord(ActionScopeType.Topic);
        Assert.Single(topicRecord.Fields);

        scopes.Set("globalKey", ActionScopeType.Global, testValue);
        RecordValue globalRecord = scopes.BuildRecord(ActionScopeType.Global);
        Assert.Single(globalRecord.Fields);

        scopes.Set("systemKey", ActionScopeType.System, testValue);
        RecordValue systemRecord = scopes.BuildRecord(ActionScopeType.System);
        Assert.Single(systemRecord.Fields);
    }

    [Fact]
    public void GetWithImplicitScope()
    {
        // Arrange
        ProcessActionScopes scopes = new();
        FormulaValue testValue = FormulaValue.New("test");
        scopes.Set("key1", ActionScopeType.Topic, testValue);

        // Act
        FormulaValue result = scopes.Get("key1");

        // Assert
        Assert.Equal(testValue, result);
    }

    [Fact]
    public void GetWithSpecifiedScope()
    {
        // Arrange
        ProcessActionScopes scopes = new();
        FormulaValue testValue = FormulaValue.New("test");
        scopes.Set("key1", ActionScopeType.Global, testValue);

        // Act
        FormulaValue result = scopes.Get("key1", ActionScopeType.Global);

        // Assert
        Assert.Equal(testValue, result);
    }

    [Fact]
    public void SetDefaultScope()
    {
        // Arrange
        ProcessActionScopes scopes = new();
        FormulaValue testValue = FormulaValue.New("test");

        // Act
        scopes.Set("key1", testValue);

        // Assert
        FormulaValue result = scopes.Get("key1", ActionScopeType.Topic);
        Assert.Equal(testValue, result);
    }

    [Fact]
    public void SetSpecifiedScope()
    {
        // Arrange
        ProcessActionScopes scopes = new();
        FormulaValue testValue = FormulaValue.New("test");

        // Act
        scopes.Set("key1", ActionScopeType.System, testValue);

        // Assert
        FormulaValue result = scopes.Get("key1", ActionScopeType.System);
        Assert.Equal(testValue, result);
    }

    [Fact]
    public void SetOverwritesExistingValue()
    {
        // Arrange
        ProcessActionScopes scopes = new();
        FormulaValue initialValue = FormulaValue.New("initial");
        FormulaValue newValue = FormulaValue.New("new");

        // Act
        scopes.Set("key1", ActionScopeType.Topic, initialValue);
        scopes.Set("key1", ActionScopeType.Topic, newValue);

        // Assert
        FormulaValue result = scopes.Get("key1", ActionScopeType.Topic);
        Assert.Equal(newValue, result);
    }
}

// Copyright (c) Microsoft. All rights reserved.
using System.Linq;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Xunit;

namespace SemanticKernel.Agents.UnitTests;

/// <summary>
/// Verify behavior of <see cref="KernelAgent"/> base class.
/// </summary>
public class KernelAgentTests
{
    /// <summary>
    /// Verify ability to merge null <see cref="KernelArguments"/>.
    /// </summary>
    [Fact]
    public void VerifyNullArgumentMerge()
    {
        // Arrange
        MockAgent agentWithNoArguments = new();
        // Act
        KernelArguments arguments = agentWithNoArguments.MergeArguments(null);
        // Assert
        Assert.Empty(arguments);

        // Arrange
        KernelArguments overrideArguments = new() { { "test", 1 } };
        // Act
        arguments = agentWithNoArguments.MergeArguments(overrideArguments);
        // Assert
        Assert.StrictEqual(1, arguments.Count);

        // Arrange
        MockAgent agentWithEmptyArguments = new() { Arguments = new() };
        // Act
        arguments = agentWithEmptyArguments.MergeArguments(null);
        // Assert
        Assert.NotNull(arguments);
        Assert.StrictEqual(agentWithEmptyArguments.Arguments, arguments);
    }

    /// <summary>
    /// Verify ability to merge <see cref="KernelArguments"/> parameters.
    /// </summary>
    [Fact]
    public void VerifyArgumentParameterMerge()
    {
        // Arrange
        MockAgent agentWithArguments = new() { Arguments = new() { { "a", 1 } } };
        KernelArguments overrideArguments = new() { { "b", 2 } };

        // Act
        KernelArguments? arguments = agentWithArguments.MergeArguments(overrideArguments);

        // Assert
        Assert.NotNull(arguments);
        Assert.Equal(2, arguments.Count);
        Assert.Equal(1, arguments["a"]);
        Assert.Equal(2, arguments["b"]);

        // Arrange
        overrideArguments["a"] = 11;
        overrideArguments["c"] = 3;

        // Act
        arguments = agentWithArguments.MergeArguments(overrideArguments);

        // Assert
        Assert.NotNull(arguments);
        Assert.Equal(3, arguments.Count);
        Assert.Equal(11, arguments["a"]);
        Assert.Equal(2, arguments["b"]);
        Assert.Equal(3, arguments["c"]);
    }

    /// <summary>
    /// Verify ability to merge <see cref="KernelArguments.ExecutionSettings"/>.
    /// </summary>
    [Fact]
    public void VerifyArgumentSettingsMerge()
    {
        // Arrange
        FunctionChoiceBehavior autoInvoke = FunctionChoiceBehavior.Auto();
        MockAgent agentWithSettings = new() { Arguments = new(new PromptExecutionSettings() { FunctionChoiceBehavior = autoInvoke }) };
        KernelArguments overrideArgumentsNoSettings = new();

        // Act
        KernelArguments? arguments = agentWithSettings.MergeArguments(overrideArgumentsNoSettings);

        // Assert
        Assert.NotNull(arguments);
        Assert.NotNull(arguments.ExecutionSettings);
        Assert.Single(arguments.ExecutionSettings);
        Assert.StrictEqual(autoInvoke, arguments.ExecutionSettings.First().Value.FunctionChoiceBehavior);

        // Arrange
        FunctionChoiceBehavior noInvoke = FunctionChoiceBehavior.None();
        KernelArguments overrideArgumentsWithSettings = new(new PromptExecutionSettings() { FunctionChoiceBehavior = noInvoke });

        // Act
        arguments = agentWithSettings.MergeArguments(overrideArgumentsWithSettings);

        // Assert
        Assert.NotNull(arguments);
        Assert.NotNull(arguments.ExecutionSettings);
        Assert.Single(arguments.ExecutionSettings);
        Assert.StrictEqual(noInvoke, arguments.ExecutionSettings.First().Value.FunctionChoiceBehavior);
    }
}

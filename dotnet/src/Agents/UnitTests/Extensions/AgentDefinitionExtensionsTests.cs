// Copyright (c) Microsoft. All rights reserved.
using System;
using System.ComponentModel;
using System.Linq;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Extensions;

/// <summary>
/// Unit testing of <see cref="AgentDefinitionExtensions"/>.
/// </summary>
public class AgentDefinitionExtensionsTests
{
    /// <summary>
    /// Verify default instance of <see cref="KernelArguments"/> can be created.
    /// </summary>
    [Fact]
    public void VerifyGetDefaultKernelArguments()
    {
        // Arrange
        var agentDefinition = new AgentDefinition();
        var kernel = new Kernel();

        // Act
        var kernelArguments = agentDefinition.GetDefaultKernelArguments(kernel);

        // Assert
        Assert.NotNull(kernelArguments);
    }

    /// <summary>
    ///  Verify default instance of <see cref="KernelArguments"/> has function calling enabled.
    /// </summary>
    [Fact]
    public void VerifyGetDefaultKernelArgumentsEnablesFunctionCalling()
    {
        // Arrange
        var agentDefinition = new AgentDefinition
        {
            Tools = [new() { Type = "function", Id = "MyPlugin.Function1" }]
        };
        var kernel = new Kernel();
        var kernelPlugin = kernel.Plugins.AddFromType<MyPlugin>();

        // Act
        var kernelArguments = agentDefinition.GetDefaultKernelArguments(kernel);

        // Assert
        Assert.NotNull(kernelArguments);
        Assert.NotNull(kernelArguments.ExecutionSettings);
        Assert.Single(kernelArguments.ExecutionSettings);
        Assert.NotNull(kernelArguments.ExecutionSettings["default"].FunctionChoiceBehavior);
        var autoFunctionChoiceBehavior = kernelArguments.ExecutionSettings["default"].FunctionChoiceBehavior as AutoFunctionChoiceBehavior;
        Assert.NotNull(autoFunctionChoiceBehavior);
        Assert.NotNull(autoFunctionChoiceBehavior.Functions);
        Assert.Single(autoFunctionChoiceBehavior.Functions);
    }

    /// <summary>
    ///  Verify instance of <see cref="KernelArguments"/> cannot be created if function is not available.
    /// </summary>
    [Fact]
    public void VerifyGetDefaultKernelArgumentsThrowsForInvalidFunction()
    {
        // Arrange
        var agentDefinition = new AgentDefinition
        {
            Tools = [new() { Type = "function", Id = "MyPlugin.Function2" }]
        };
        var kernel = new Kernel();
        var kernelPlugin = kernel.Plugins.AddFromType<MyPlugin>();

        // Act & Assert
        Assert.Throws<KernelException>(() => agentDefinition.GetDefaultKernelArguments(kernel));
    }

    /// <summary>
    /// Verify GetPromptTemplate returns null if there is no template factory, template or instructions.
    /// </summary>
    [Fact]
    public void VerifyGetPromptTemplateReturnsNull()
    {
        // Arrange
        var agentDefinition = new AgentDefinition();
        var kernel = new Kernel();

        // Act & Assert
        Assert.Null(agentDefinition.GetPromptTemplate(kernel, null));
    }

    /// <summary>
    /// Verify GetPromptTemplate returns null if there is no template factory, template or instructions.
    /// </summary>
    [Fact]
    public void VerifyGetPromptTemplate()
    {
        // Arrange
        var agentDefinition = new AgentDefinition()
        {
            Instructions = "instructions",
            Template = new() { Format = "semantic-kernel" }
        };
        var kernel = new Kernel();
        var templateFactory = new KernelPromptTemplateFactory();

        // Act
        var promptTemplate = agentDefinition.GetPromptTemplate(kernel, templateFactory);

        // Assert
        Assert.NotNull(promptTemplate);
    }

    /// <summary>
    ///  Verify GetFirstToolDefinition returns the correct tool.
    /// </summary>
    [Fact]
    public void VerifyGetFirstToolDefinition()
    {
        // Arrange
        var agentDefinition = new AgentDefinition
        {
            Tools =
            [
                new() { Type = "function", Id = "MyPlugin.Function1" },
                new() { Type = "code_interpreter" }
            ]
        };
        var kernel = new Kernel();
        var kernelPlugin = kernel.Plugins.AddFromType<MyPlugin>();

        // Act
        var toolDefinition = agentDefinition.GetFirstToolDefinition("function");

        // Assert
        Assert.NotNull(toolDefinition);
        Assert.Equal("function", toolDefinition.Type);
    }

    /// <summary>
    ///  Verify GetToolDefinitions returns the correct tools.
    /// </summary>
    [Fact]
    public void VerifyGetToolDefinitions()
    {
        // Arrange
        var agentDefinition = new AgentDefinition
        {
            Tools =
            [
                new() { Type = "function", Id = "MyPlugin.Function1" },
                new() { Type = "function", Id = "MyPlugin.Function2" },
                new() { Type = "code_interpreter" }
            ]
        };
        var kernel = new Kernel();
        var kernelPlugin = kernel.Plugins.AddFromType<MyPlugin>();

        // Act
        var toolDefinitions = agentDefinition.GetToolDefinitions("function");

        // Assert
        Assert.NotNull(toolDefinitions);
        Assert.Equal(2, toolDefinitions.Count());
    }

    /// <summary>
    ///  Verify HasToolType returns the correct values.
    /// </summary>
    [Fact]
    public void VerifyHasToolType()
    {
        // Arrange
        var agentDefinition = new AgentDefinition
        {
            Tools =
            [
                new() { Type = "function", Id = "MyPlugin.Function1" },
                new() { Type = "code_interpreter" }
            ]
        };
        var kernel = new Kernel();
        var kernelPlugin = kernel.Plugins.AddFromType<MyPlugin>();

        // Act & Assert
        Assert.True(agentDefinition.HasToolType("function"));
        Assert.True(agentDefinition.HasToolType("code_interpreter"));
        Assert.False(agentDefinition.HasToolType("file_search"));
    }

    #region private
    private sealed class MyPlugin
    {
        [KernelFunction("Function1")]
        [Description("Description for function 1.")]
        public string Function1([Description("Description for parameter 1")] string param1) => $"Function1: {param1}";
    }
    #endregion
}

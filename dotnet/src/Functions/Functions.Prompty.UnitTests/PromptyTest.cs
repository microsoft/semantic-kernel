// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Functions.Prompty.UnitTests;
public sealed class PromptyTest
{
    [Fact]
    public void ChatPromptyTest()
    {
        // Arrange
        var kernel = Kernel.CreateBuilder()
            .Build();

        var cwd = Directory.GetCurrentDirectory();
        var chatPromptyPath = Path.Combine(cwd, "TestData", "chat.prompty");
        var promptyTemplate = File.ReadAllText(chatPromptyPath);

        // Act
        var kernelFunction = kernel.CreateFunctionFromPrompty(promptyTemplate);

        // Assert
        Assert.Equal("Contoso_Chat_Prompt", kernelFunction.Name);
        Assert.Equal("A retail assistant for Contoso Outdoors products retailer.", kernelFunction.Description);

        // chat prompty doesn't contain input parameters
        Assert.Empty(kernelFunction.Metadata.Parameters);
    }

    [Fact]
    public void ChatPromptyShouldSupportCreatingOpenAIExecutionSettings()
    {
        // Arrange
        var kernel = Kernel.CreateBuilder()
            .Build();

        var cwd = Directory.GetCurrentDirectory();
        var chatPromptyPath = Path.Combine(cwd, "TestData", "chat.prompty");

        // Act
        var kernelFunction = kernel.CreateFunctionFromPromptyFile(chatPromptyPath);

        // Assert
        // kernel function created from chat.prompty should have a single execution setting
        Assert.Single(kernelFunction.ExecutionSettings!);
        Assert.True(kernelFunction.ExecutionSettings!.ContainsKey("default"));

        // Arrange
        var defaultExecutionSetting = kernelFunction.ExecutionSettings["default"];

        // Act
        var executionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(defaultExecutionSetting);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal("gpt-35-turbo", executionSettings.ModelId);
        Assert.Equal(1.0, executionSettings.Temperature);
        Assert.Equal(1.0, executionSettings.TopP);
        Assert.Null(executionSettings.StopSequences);
        Assert.Null(executionSettings.ResponseFormat);
        Assert.Null(executionSettings.TokenSelectionBiases);
        Assert.Null(executionSettings.MaxTokens);
        Assert.Null(executionSettings.Seed);
    }

    [Fact]
    public void ItShouldCreateFunctionFromPromptYamlWithNoExecutionSettings()
    {
        // Arrange
        var kernel = Kernel.CreateBuilder()
            .Build();
        var cwd = Directory.GetCurrentDirectory();
        var promptyPath = Path.Combine(cwd, "TestData", "chatNoExecutionSettings.prompty");

        // Act
        var kernelFunction = kernel.CreateFunctionFromPromptyFile(promptyPath);

        // Assert
        Assert.NotNull(kernelFunction);
        Assert.Equal("prompty_with_no_execution_setting", kernelFunction.Name);
        Assert.Equal("prompty without execution setting", kernelFunction.Description);
        Assert.Single(kernelFunction.Metadata.Parameters);
        Assert.Empty(kernelFunction.ExecutionSettings!);
    }
}

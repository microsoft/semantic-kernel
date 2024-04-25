// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Prompty.Extension;
using Xunit;

namespace SemanticKernel.Functions.Prompty.UnitTests;
public sealed class PromptyTest
{
    [Fact]
    public void ChatPromptyTest()
    {
        var kernel = Kernel.CreateBuilder()
            .Build();

        var cwd = Directory.GetCurrentDirectory();
        var chatPromptyPath = Path.Combine(cwd, "TestData", "chat.prompty");
        var kernelFunction = kernel.CreateFunctionFromPrompty(chatPromptyPath);

        Assert.Equal("Contoso_Chat_Prompt", kernelFunction.Name);
        Assert.Equal("A retail assistant for Contoso Outdoors products retailer.", kernelFunction.Description);

        // chat prompty doesn't contain input parameters
        Assert.Empty(kernelFunction.Metadata.Parameters);
    }

    [Fact]
    public void ChatPromptyShouldSupportCreatingOpenAIExecutionSettings()
    {
        var kernel = Kernel.CreateBuilder()
            .Build();

        var cwd = Directory.GetCurrentDirectory();
        var chatPromptyPath = Path.Combine(cwd, "TestData", "chat.prompty");
        var kernelFunction = kernel.CreateFunctionFromPrompty(chatPromptyPath);

        // kernel function created from chat.prompty should have a single execution setting
        Assert.Single(kernelFunction.ExecutionSettings!);
        Assert.True(kernelFunction.ExecutionSettings!.ContainsKey("default"));

        var defaultExecutionSetting = kernelFunction.ExecutionSettings["default"];

        // Act
        var executionSettings = OpenAIPromptExecutionSettings.FromExecutionSettings(defaultExecutionSetting);

        // Assert
        Assert.NotNull(executionSettings);
        Assert.Equal("gpt-35-turbo", executionSettings.ModelId);
        Assert.Equal(1.0, executionSettings.Temperature);
        Assert.Equal(1.0, executionSettings.TopP);
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public sealed class KernelFunctionUnitTestStrategies
{
    [Fact]
    public async Task CreateFromFunctionDelegateVoidAsync()
    {
        // Arrange
        var kernel = new Kernel();
        object expected = new();
        object FunctionDelegate() => expected;
        var function = KernelFunctionFactory.CreateFromMethod(FunctionDelegate, "MyFunction");

        // Act
        var result = await function.InvokeAsync(kernel);

        // Assert
        Assert.Equal(expected, result.GetValue<object>());
    }

    [Fact]
    public async Task CreatePluginFromFunctionDelegateVoidAsync()
    {
        // Arrange
        var kernel = new Kernel();
        object expected = new();
        object FunctionDelegate() => expected;
        var function = KernelFunctionFactory.CreateFromMethod(FunctionDelegate, "MyFunction");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [function]);
        kernel.Plugins.Add(plugin);

        // Act
        var result = await kernel.InvokeAsync("MyPlugin", "MyFunction");

        // Assert
        Assert.Equal(expected, result.GetValue<object>());
    }

    [Fact]
    public async Task CreatePluginFromMockObjectAsync()
    {
        // Arrange
        var kernel = new Kernel();
        object expected = new();
        Mock<MyPlugin> mockPlugin = new();
        mockPlugin.Setup(m => m.MyFunction(It.IsAny<string>(), It.IsAny<int>())).Returns(expected);
        var plugin = KernelPluginFactory.CreateFromObject(mockPlugin.Object, "MyPlugin");
        kernel.Plugins.Add(plugin);

        // Act
        var arguments = new KernelArguments
        {
            { "param1", "value1" },
            { "param2", 2 }
        };
        var result = await kernel.InvokeAsync("MyPlugin", "MyFunction", arguments);

        // Assert
        Assert.Equal(expected, result.GetValue<object>());
        mockPlugin.Verify(mock => mock.MyFunction("value1", 2), Times.Once());
    }

    [Fact]
    public async Task MockChatCompletionServiceForPromptAsync()
    {
        // Arrange
        var mockService = new Mock<IChatCompletionService>();
        var mockResult = mockService
            .Setup(s => s.GetChatMessageContentsAsync(It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync([new(AuthorRole.User, "Expected response")]);
        KernelBuilder builder = new();
        builder.Services.AddTransient<IChatCompletionService>((sp) => mockService.Object);
        Kernel kernel = builder.Build();
        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Some prompt");

        // Act
        var result = await kernel.InvokeAsync(function);

        // Assert
        Assert.Equal("Expected response", result.GetValue<string>());
    }

    public class MyPlugin
    {
        [KernelFunction]
        public virtual object MyFunction(string param1, int param2)
        {
            return new();
        }
    }
}

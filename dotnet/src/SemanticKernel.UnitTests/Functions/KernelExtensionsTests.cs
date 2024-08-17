// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.TextGeneration;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class KernelExtensionsTests
{
    [Fact]
    public void CreatePluginFromFunctions()
    {
        Kernel kernel = new();

        KernelPlugin plugin = kernel.CreatePluginFromFunctions("coolplugin",
        [
            kernel.CreateFunctionFromMethod(() => { }, "Function1"),
            kernel.CreateFunctionFromMethod(() => { }, "Function2"),
        ]);

        Assert.NotNull(plugin);
        Assert.Empty(kernel.Plugins);

        Assert.Equal("coolplugin", plugin.Name);
        Assert.Empty(plugin.Description);
        Assert.Equal(2, plugin.FunctionCount);
        Assert.True(plugin.Contains("Function1"));
        Assert.True(plugin.Contains("Function2"));
    }

    [Fact]
    public void CreateEmptyPluginFromFunctions()
    {
        Kernel kernel = new();

        KernelPlugin plugin = kernel.CreatePluginFromFunctions("coolplugin");

        Assert.NotNull(plugin);
        Assert.Empty(kernel.Plugins);

        Assert.Equal("coolplugin", plugin.Name);
        Assert.Empty(plugin.Description);
        Assert.Empty(plugin);
        Assert.Equal(0, plugin.FunctionCount);
    }

    [Fact]
    public void CreatePluginFromDescriptionAndFunctions()
    {
        Kernel kernel = new();

        KernelPlugin plugin = kernel.CreatePluginFromFunctions("coolplugin", "the description",
        [
            kernel.CreateFunctionFromMethod(() => { }, "Function1"),
            kernel.CreateFunctionFromMethod(() => { }, "Function2"),
        ]);

        Assert.NotNull(plugin);
        Assert.Empty(kernel.Plugins);

        Assert.Equal("coolplugin", plugin.Name);
        Assert.Equal("the description", plugin.Description);
        Assert.Equal(2, plugin.FunctionCount);
        Assert.True(plugin.Contains("Function1"));
        Assert.True(plugin.Contains("Function2"));
    }

    [Fact]
    public async Task CreateFunctionFromPromptWithMultipleSettingsUseCorrectServiceAsync()
    {
        // Arrange
        var mockTextGeneration1 = new Mock<ITextGenerationService>();
        var mockTextGeneration2 = new Mock<IChatCompletionService>();
        var fakeTextContent = new TextContent("llmResult");
        var fakeChatContent = new ChatMessageContent(AuthorRole.User, "content");

        mockTextGeneration1.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([fakeTextContent]);
        mockTextGeneration2.Setup(c => c.GetChatMessageContentsAsync(It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([fakeChatContent]);

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton("service1", mockTextGeneration1.Object);
        builder.Services.AddKeyedSingleton("service2", mockTextGeneration2.Object);
        builder.Services.AddKeyedSingleton("service3", mockTextGeneration1.Object);
        Kernel kernel = builder.Build();

        KernelFunction function = kernel.CreateFunctionFromPrompt("coolfunction", [
            new PromptExecutionSettings { ServiceId = "service5" }, // Should ignore this as service5 is not registered
            new PromptExecutionSettings { ServiceId = "service2" },
        ]);

        // Act
        await kernel.InvokeAsync(function);

        // Assert
        mockTextGeneration1.Verify(a => a.GetTextContentsAsync("coolfunction", It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Never());
        mockTextGeneration2.Verify(a => a.GetChatMessageContentsAsync(It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public void ImportPluginFromFunctions()
    {
        Kernel kernel = new();

        kernel.ImportPluginFromFunctions("coolplugin",
        [
            kernel.CreateFunctionFromMethod(() => { }, "Function1"),
            kernel.CreateFunctionFromMethod(() => { }, "Function2"),
        ]);

        Assert.Single(kernel.Plugins);

        KernelPlugin plugin = kernel.Plugins["coolplugin"];
        Assert.Equal("coolplugin", plugin.Name);
        Assert.Empty(plugin.Description);
        Assert.NotNull(plugin);

        Assert.Equal(2, plugin.FunctionCount);
        Assert.True(plugin.Contains("Function1"));
        Assert.True(plugin.Contains("Function2"));
    }

    [Fact]
    public void ImportPluginFromDescriptionAndFunctions()
    {
        Kernel kernel = new();

        kernel.ImportPluginFromFunctions("coolplugin", "the description",
        [
            kernel.CreateFunctionFromMethod(() => { }, "Function1"),
            kernel.CreateFunctionFromMethod(() => { }, "Function2"),
        ]);

        Assert.Single(kernel.Plugins);

        KernelPlugin plugin = kernel.Plugins["coolplugin"];
        Assert.Equal("coolplugin", plugin.Name);
        Assert.Equal("the description", plugin.Description);
        Assert.NotNull(plugin);

        Assert.Equal(2, plugin.FunctionCount);
        Assert.True(plugin.Contains("Function1"));
        Assert.True(plugin.Contains("Function2"));
    }

    [Fact]
    public void AddFromFunctions()
    {
        Kernel kernel = new();

        kernel.Plugins.AddFromFunctions("coolplugin",
        [
            kernel.CreateFunctionFromMethod(() => { }, "Function1"),
            kernel.CreateFunctionFromMethod(() => { }, "Function2"),
        ]);

        Assert.Single(kernel.Plugins);

        KernelPlugin plugin = kernel.Plugins["coolplugin"];
        Assert.Equal("coolplugin", plugin.Name);
        Assert.Empty(plugin.Description);
        Assert.NotNull(plugin);

        Assert.Equal(2, plugin.FunctionCount);
        Assert.True(plugin.Contains("Function1"));
        Assert.True(plugin.Contains("Function2"));
    }

    [Fact]
    public void AddFromDescriptionAndFunctions()
    {
        Kernel kernel = new();

        kernel.Plugins.AddFromFunctions("coolplugin", "the description",
        [
            kernel.CreateFunctionFromMethod(() => { }, "Function1"),
            kernel.CreateFunctionFromMethod(() => { }, "Function2"),
        ]);

        Assert.Single(kernel.Plugins);

        KernelPlugin plugin = kernel.Plugins["coolplugin"];
        Assert.Equal("coolplugin", plugin.Name);
        Assert.Equal("the description", plugin.Description);
        Assert.NotNull(plugin);

        Assert.Equal(2, plugin.FunctionCount);
        Assert.True(plugin.Contains("Function1"));
        Assert.True(plugin.Contains("Function2"));
    }
}

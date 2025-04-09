// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.TextGeneration;
using Moq;
using SemanticKernel.UnitTests.Functions.JsonSerializerContexts;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class KernelExtensionsCreateFunctionFromPromptTests
{
    private readonly Kernel _kernel;

    public KernelExtensionsCreateFunctionFromPromptTests()
    {
        var mockService = new Mock<IChatCompletionService>();
        mockService
            .Setup(s => s.GetChatMessageContentsAsync(It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings?>(), It.IsAny<Kernel?>(), It.IsAny<CancellationToken>()))
            .Returns((ChatHistory ch, PromptExecutionSettings? _, Kernel? _, CancellationToken _) => Task.FromResult((IReadOnlyList<ChatMessageContent>)[new(AuthorRole.Assistant, ch.First().Content)]));

        var builder = new KernelBuilder();
        builder.Services.AddSingleton<IChatCompletionService>(mockService.Object);

        this._kernel = builder.Build();
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

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldCreateFunctionFromStringPromptUsingOverloadWithPromptExecutionSettings(JsonSerializerOptions? jsos)
    {
        // Arrange & Act
        KernelFunction function = jsos is not null ?
            function = this._kernel.CreateFunctionFromPrompt("Prompt with {{$A}} variable", jsonSerializerOptions: jsos, executionSettings: new PromptExecutionSettings()) :
            function = this._kernel.CreateFunctionFromPrompt("Prompt with {{$A}} variable", executionSettings: new PromptExecutionSettings());

        // Assert
        await this.AssertFunction(function);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldCreateFunctionFromStringPromptUsingOverloadWithListOfPromptExecutionSettings(JsonSerializerOptions? jsos)
    {
        // Arrange & Act
        KernelFunction function = jsos is not null ?
            function = this._kernel.CreateFunctionFromPrompt("Prompt with {{$A}} variable", jsonSerializerOptions: jsos, executionSettings: [new PromptExecutionSettings()]) :
            function = this._kernel.CreateFunctionFromPrompt("Prompt with {{$A}} variable", executionSettings: [new PromptExecutionSettings()]);

        // Assert
        await this.AssertFunction(function);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldCreateFunctionFromPromptTemplateConfig(JsonSerializerOptions? jsos)
    {
        // Arrange & Act
        KernelFunction function = jsos is not null ?
            function = this._kernel.CreateFunctionFromPrompt(new PromptTemplateConfig("Prompt with {{$A}} variable"), jsonSerializerOptions: jsos) :
            function = this._kernel.CreateFunctionFromPrompt(new PromptTemplateConfig("Prompt with {{$A}} variable"));

        // Assert
        await this.AssertFunction(function);
    }

    private async Task AssertFunction(KernelFunction function)
    {
        Assert.NotEmpty(function.Metadata.Parameters);
        Assert.NotNull(function.Metadata.Parameters[0].Schema);
        Assert.Equal("{\"type\":\"string\"}", function.Metadata.Parameters[0].Schema!.ToString());

        Assert.NotNull(function.Metadata.ReturnParameter);
        Assert.Null(function.Metadata.ReturnParameter.Schema);

        // Assert invocation
        var invokeResult = await function.InvokeAsync(this._kernel, new() { ["A"] = "a" });
        var result = invokeResult?.GetValue<string>();
        Assert.Equal("Prompt with a variable", result);
    }
}

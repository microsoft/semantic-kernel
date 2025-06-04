// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using SemanticKernel.UnitTests.Functions.JsonSerializerContexts;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class KernelFunctionFactoryCreateFromPromptTests
{
    private readonly Kernel _kernel;

    public KernelFunctionFactoryCreateFromPromptTests()
    {
        var mockService = new Mock<IChatCompletionService>();
        mockService
            .Setup(s => s.GetChatMessageContentsAsync(It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings?>(), It.IsAny<Kernel?>(), It.IsAny<CancellationToken>()))
            .Returns((ChatHistory ch, PromptExecutionSettings? _, Kernel? _, CancellationToken _) => Task.FromResult((IReadOnlyList<ChatMessageContent>)[new(AuthorRole.Assistant, ch.First().Content)]));

        var builder = new KernelBuilder();
        builder.Services.AddSingleton<IChatCompletionService>(mockService.Object);

        this._kernel = builder.Build();
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldCreateFunctionFromStringPromptUsingOverloadWithPromptExecutionSettings(JsonSerializerOptions? jsos)
    {
        // Arrange & Act
        KernelFunction function = jsos is not null ?
            function = KernelFunctionFactory.CreateFromPrompt("Prompt with {{$A}} variable", jsonSerializerOptions: jsos, executionSettings: new PromptExecutionSettings()) :
            function = KernelFunctionFactory.CreateFromPrompt("Prompt with {{$A}} variable", executionSettings: new PromptExecutionSettings());

        // Assert
        await this.AssertFunction(function);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldCreateFunctionFromStringPromptUsingOverloadWithListOfPromptExecutionSettings(JsonSerializerOptions? jsos)
    {
        // Arrange & Act
        KernelFunction function = jsos is not null ?
            function = KernelFunctionFactory.CreateFromPrompt("Prompt with {{$A}} variable", jsonSerializerOptions: jsos, executionSettings: [new PromptExecutionSettings()]) :
            function = KernelFunctionFactory.CreateFromPrompt("Prompt with {{$A}} variable", executionSettings: [new PromptExecutionSettings()]);

        // Assert
        await this.AssertFunction(function);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldCreateFunctionFromPromptTemplateConfig(JsonSerializerOptions? jsos)
    {
        // Arrange & Act
        KernelFunction function = jsos is not null ?
            function = KernelFunctionFactory.CreateFromPrompt(new PromptTemplateConfig("Prompt with {{$A}} variable"), jsonSerializerOptions: jsos) :
            function = KernelFunctionFactory.CreateFromPrompt(new PromptTemplateConfig("Prompt with {{$A}} variable"));

        // Assert
        await this.AssertFunction(function);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldCreateFunctionFromPromptTemplateAndConfig(JsonSerializerOptions? jsos)
    {
        // Arrange
        var promptTemplateMock = new Mock<IPromptTemplate>();
        promptTemplateMock
            .Setup(p => p.RenderAsync(It.IsAny<Kernel>(), It.IsAny<KernelArguments?>(), It.IsAny<CancellationToken>()))
            .Returns((Kernel _, KernelArguments? _, CancellationToken _) => Task.FromResult("Prompt with a variable"));

        var promptTemplateConfig = new PromptTemplateConfig() { InputVariables = [new() { Name = "A" }] };

        // Act
        KernelFunction function = jsos is not null ?
            function = KernelFunctionFactory.CreateFromPrompt(promptTemplateMock.Object, promptConfig: promptTemplateConfig, jsonSerializerOptions: jsos) :
            function = KernelFunctionFactory.CreateFromPrompt(promptTemplateMock.Object, promptConfig: promptTemplateConfig);

        // Assert
        await this.AssertFunction(function);
    }

    private async Task AssertFunction(KernelFunction function)
    {
        // Assert schema
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

// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text;
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

public class KernelExtensionsInvokePromptTests
{
    private readonly Kernel _kernel;

    public KernelExtensionsInvokePromptTests()
    {
#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
        static async IAsyncEnumerable<StreamingChatMessageContent> GetSingleElementAsyncEnumerable(string? content)
        {
            yield return new StreamingChatMessageContent(AuthorRole.Assistant, content);
        }
#pragma warning restore CS1998 // Async method lacks 'await' operators and will run synchronously

        var mockService = new Mock<IChatCompletionService>();
        mockService
            .Setup(s => s.GetChatMessageContentsAsync(It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings?>(), It.IsAny<Kernel?>(), It.IsAny<CancellationToken>()))
            .Returns((ChatHistory ch, PromptExecutionSettings? _, Kernel? _, CancellationToken _) => Task.FromResult((IReadOnlyList<ChatMessageContent>)[new(AuthorRole.Assistant, ch.First().Content)]));
        mockService
            .Setup(s => s.GetStreamingChatMessageContentsAsync(It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings?>(), It.IsAny<Kernel?>(), It.IsAny<CancellationToken>()))
            .Returns((ChatHistory ch, PromptExecutionSettings? _, Kernel? _, CancellationToken _) => GetSingleElementAsyncEnumerable(ch.First().Content));

        var builder = new KernelBuilder();
        builder.Services.AddSingleton<IChatCompletionService>(mockService.Object);

        this._kernel = builder.Build();
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldInvokePromptAndReturnResultAsFunctionResult(JsonSerializerOptions? jsos)
    {
        // Act
        FunctionResult invokeResult = jsos is not null ?
            invokeResult = await this._kernel.InvokePromptAsync(jsonSerializerOptions: jsos, promptTemplate: "Prompt with {{$A}} variable", arguments: new() { ["A"] = "a" }) :
            invokeResult = await this._kernel.InvokePromptAsync(promptTemplate: "Prompt with {{$A}} variable", arguments: new() { ["A"] = "a" });

        // Assert
        var result = invokeResult?.GetValue<string>();
        Assert.Equal("Prompt with a variable", result);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldInvokePromptAndReturnResultOfSpecifiedType(JsonSerializerOptions? jsos)
    {
        // Act
        string? result = jsos is not null ?
            result = await this._kernel.InvokePromptAsync<string>(jsonSerializerOptions: jsos, promptTemplate: "Prompt with {{$A}} variable", arguments: new() { ["A"] = "a" }) :
            result = await this._kernel.InvokePromptAsync<string>(promptTemplate: "Prompt with {{$A}} variable", arguments: new() { ["A"] = "a" });

        // Assert
        Assert.Equal("Prompt with a variable", result);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldInvokePromptUsingStreamingAndReturnResultAsFunctionResult(JsonSerializerOptions? jsos)
    {
        // Act
        IAsyncEnumerable<StreamingKernelContent> streamingContent = jsos is not null ?
            streamingContent = this._kernel.InvokePromptStreamingAsync(jsonSerializerOptions: jsos, promptTemplate: "Prompt with {{$A}} variable", arguments: new() { ["A"] = "a" }) :
            streamingContent = this._kernel.InvokePromptStreamingAsync(promptTemplate: "Prompt with {{$A}} variable", arguments: new() { ["A"] = "a" });

        // Assert
        StringBuilder builder = new();

        await foreach (var content in streamingContent)
        {
            builder.Append(content.ToString());
        }

        Assert.Equal("Prompt with a variable", builder.ToString());
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldInvokePromptUsingStreamingAndReturnResultOfSpecifiedType(JsonSerializerOptions? jsos)
    {
        // Act
        IAsyncEnumerable<string> streamingContent = jsos is not null ?
            streamingContent = this._kernel.InvokePromptStreamingAsync<string>(jsonSerializerOptions: jsos, promptTemplate: "Prompt with {{$A}} variable", arguments: new() { ["A"] = "a" }) :
            streamingContent = this._kernel.InvokePromptStreamingAsync<string>(promptTemplate: "Prompt with {{$A}} variable", arguments: new() { ["A"] = "a" });

        // Assert
        StringBuilder builder = new();

        await foreach (var content in streamingContent)
        {
            builder.Append(content);
        }

        Assert.Equal("Prompt with a variable", builder.ToString());
    }
}

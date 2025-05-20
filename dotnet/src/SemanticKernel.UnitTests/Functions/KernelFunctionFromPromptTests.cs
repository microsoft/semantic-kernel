// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.TextGeneration;
using Moq;
using SemanticKernel.UnitTests.Functions.JsonSerializerContexts;
using Xunit;
using MEAI = Microsoft.Extensions.AI;

namespace SemanticKernel.UnitTests.Functions;

public class KernelFunctionFromPromptTests
{
    [Fact]
    public void ItAddsMissingVariablesForPrompt()
    {
        // Arrange & Act
        var function = KernelFunctionFromPrompt.Create("This {{$x11}} {{$a}}{{$missing}} test template {{p.bar $b}} and {{p.foo c='literal \"c\"' d = $d}} and {{p.baz ename=$e}}");

        // Assert
        Assert.NotNull(function);
        Assert.NotNull(function.Metadata);
        Assert.NotNull(function.Metadata.Parameters);
        Assert.Equal(6, function.Metadata.Parameters.Count);
        Assert.Equal("x11", function.Metadata.Parameters[0].Name);
        Assert.Equal("a", function.Metadata.Parameters[1].Name);
        Assert.Equal("missing", function.Metadata.Parameters[2].Name);
        Assert.Equal("b", function.Metadata.Parameters[3].Name);
        Assert.Equal("d", function.Metadata.Parameters[4].Name);
        Assert.Equal("e", function.Metadata.Parameters[5].Name);
    }

    [Fact]
    public void ItProvidesAccessToFunctionsViaFunctionCollection()
    {
        // Arrange
        var factory = new Mock<Func<IServiceProvider, ITextGenerationService>>();
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton(factory.Object);
        Kernel kernel = builder.Build();

        kernel.ImportPluginFromFunctions("jk", functions: [kernel.CreateFunctionFromPrompt(promptTemplate: "Tell me a joke", functionName: "joker", description: "Nice fun")]);

        // Act & Assert - 3 functions, var name is not case sensitive
        Assert.True(kernel.Plugins.TryGetFunction("jk", "joker", out _));
        Assert.True(kernel.Plugins.TryGetFunction("JK", "JOKER", out _));
    }

    [Theory]
    [InlineData(null, null)]
    [InlineData("My Chat Prompt", "My Chat Prompt")]
    public async Task ItUsesChatSystemPromptWhenProvidedAsync(string? providedSystemChatPrompt, string? expectedSystemChatPrompt)
    {
        // Arrange
        var mockTextGeneration = new Mock<ITextGenerationService>();
        var fakeTextContent = new TextContent("llmResult");

        mockTextGeneration.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([fakeTextContent]);

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton("x", mockTextGeneration.Object);
        Kernel kernel = builder.Build();

        var openAIExecutionSettings = providedSystemChatPrompt is null
            ? new OpenAIPromptExecutionSettings()
            : new OpenAIPromptExecutionSettings
            {
                ChatSystemPrompt = providedSystemChatPrompt
            };

        var promptConfig = new PromptTemplateConfig("template");
        promptConfig.AddExecutionSettings(openAIExecutionSettings);
        var func = kernel.CreateFunctionFromPrompt(promptConfig);

        // Act
        await kernel.InvokeAsync(func);

        // Assert
        mockTextGeneration.Verify(a => a.GetTextContentsAsync("template", It.Is<OpenAIPromptExecutionSettings>(c => c.ChatSystemPrompt == expectedSystemChatPrompt), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task ItUsesServiceIdWhenProvidedAsync()
    {
        // Arrange
        var mockTextGeneration1 = new Mock<ITextGenerationService>();
        var mockTextGeneration2 = new Mock<ITextGenerationService>();
        var fakeTextContent = new TextContent("llmResult");

        mockTextGeneration1.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([fakeTextContent]);
        mockTextGeneration2.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([fakeTextContent]);

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton("service1", mockTextGeneration1.Object);
        builder.Services.AddKeyedSingleton("service2", mockTextGeneration2.Object);
        Kernel kernel = builder.Build();

        var promptConfig = new PromptTemplateConfig("template");
        promptConfig.AddExecutionSettings(new PromptExecutionSettings(), "service1");
        var func = kernel.CreateFunctionFromPrompt(promptConfig);

        // Act
        await kernel.InvokeAsync(func);

        // Assert
        mockTextGeneration1.Verify(a => a.GetTextContentsAsync("template", It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
        mockTextGeneration2.Verify(a => a.GetTextContentsAsync("template", It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Never());
    }

    [Fact]
    public async Task ItUsesServiceIdWhenProvidedInMethodAsync()
    {
        // Arrange
        var mockTextGeneration1 = new Mock<ITextGenerationService>();
        var mockTextGeneration2 = new Mock<ITextGenerationService>();
        var fakeTextContent = new TextContent("llmResult");

        mockTextGeneration1.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([fakeTextContent]);
        mockTextGeneration2.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([fakeTextContent]);

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton("service1", mockTextGeneration1.Object);
        builder.Services.AddKeyedSingleton("service2", mockTextGeneration2.Object);
        Kernel kernel = builder.Build();

        var func = kernel.CreateFunctionFromPrompt("my prompt", [new PromptExecutionSettings { ServiceId = "service2" }]);

        // Act
        await kernel.InvokeAsync(func);

        // Assert
        mockTextGeneration1.Verify(a => a.GetTextContentsAsync("my prompt", It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Never());
        mockTextGeneration2.Verify(a => a.GetTextContentsAsync("my prompt", It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task ItUsesChatServiceIdWhenProvidedInMethodAsync()
    {
        // Arrange
        var mockTextGeneration = new Mock<ITextGenerationService>();
        var mockChatCompletion = new Mock<IChatCompletionService>();
        var fakeTextContent = new TextContent("llmResult");
        var fakeChatContent = new ChatMessageContent(AuthorRole.User, "content");

        mockTextGeneration.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([fakeTextContent]);
        mockChatCompletion.Setup(c => c.GetChatMessageContentsAsync(It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([fakeChatContent]);

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton("service1", mockTextGeneration.Object);
        builder.Services.AddKeyedSingleton("service2", mockChatCompletion.Object);
        builder.Services.AddKeyedSingleton("service3", mockTextGeneration.Object);
        Kernel kernel = builder.Build();

        var func = kernel.CreateFunctionFromPrompt("my prompt", [new PromptExecutionSettings { ServiceId = "service2" }]);

        // Act
        await kernel.InvokeAsync(func);

        // Assert
        mockTextGeneration.Verify(a => a.GetTextContentsAsync("my prompt", It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Never());
        mockChatCompletion.Verify(a => a.GetChatMessageContentsAsync(It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task ItUsesChatClientIdWhenProvidedInMethodAsync()
    {
        // Arrange
        var mockTextGeneration = new Mock<ITextGenerationService>();
        var mockChatCompletion = new Mock<IChatCompletionService>();
        var mockChatClient = new Mock<MEAI.IChatClient>();
        var fakeTextContent = new TextContent("llmResult");
        var fakeChatContent = new ChatMessageContent(AuthorRole.User, "content");
        var fakeChatResponse = new MEAI.ChatResponse(new MEAI.ChatMessage());

        mockTextGeneration.Setup(c => c.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([fakeTextContent]);
        mockChatCompletion.Setup(c => c.GetChatMessageContentsAsync(It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([fakeChatContent]);
        mockChatClient.Setup(c => c.GetResponseAsync(It.IsAny<IList<MEAI.ChatMessage>>(), It.IsAny<MEAI.ChatOptions>(), It.IsAny<CancellationToken>())).ReturnsAsync(fakeChatResponse);
        mockChatClient.Setup(c => c.GetService(typeof(MEAI.ChatClientMetadata), It.IsAny<object?>())).Returns(new MEAI.ChatClientMetadata());

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton("service1", mockTextGeneration.Object);
        builder.Services.AddKeyedSingleton("service2", mockChatClient.Object);
        builder.Services.AddKeyedSingleton("service3", mockChatCompletion.Object);
        Kernel kernel = builder.Build();

        var func = kernel.CreateFunctionFromPrompt("my prompt", [new PromptExecutionSettings { ServiceId = "service2" }]);

        // Act
        await kernel.InvokeAsync(func);

        // Assert
        mockTextGeneration.Verify(a => a.GetTextContentsAsync("my prompt", It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Never());
        mockChatCompletion.Verify(a => a.GetChatMessageContentsAsync(It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Never());
        mockChatClient.Verify(a => a.GetResponseAsync(It.IsAny<IList<MEAI.ChatMessage>>(), It.IsAny<MEAI.ChatOptions>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task ItFailsIfInvalidServiceIdIsProvidedAsync()
    {
        // Arrange
        var mockTextGeneration1 = new Mock<ITextGenerationService>();
        var mockTextGeneration2 = new Mock<ITextGenerationService>();

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton("service1", mockTextGeneration1.Object);
        builder.Services.AddKeyedSingleton("service2", mockTextGeneration2.Object);
        Kernel kernel = builder.Build();

        var promptConfig = new PromptTemplateConfig("template");
        promptConfig.AddExecutionSettings(new PromptExecutionSettings(), "service3");
        var func = kernel.CreateFunctionFromPrompt(promptConfig);

        // Act
        var exception = await Assert.ThrowsAsync<KernelException>(() => kernel.InvokeAsync(func));

        // Assert
        Assert.Contains("Expected serviceIds: service3.", exception.Message);
    }

    [Fact]
    public async Task ItParsesStandardizedPromptWhenServiceIsChatCompletionAsync()
    {
        var fakeService = new FakeChatAsTextService();
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<ITextGenerationService>((sp) => fakeService);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("""
            <message role="system">You are a helpful assistant.</message>
            <message role="user">How many 20 cents can I get from 1 dollar?</message>
            """);

        // Act + Assert
        await kernel.InvokeAsync(function);

        Assert.NotNull(fakeService.ChatHistory);
        Assert.Equal(2, fakeService.ChatHistory.Count);
        Assert.Equal("You are a helpful assistant.", fakeService.ChatHistory[0].Content);
        Assert.Equal("How many 20 cents can I get from 1 dollar?", fakeService.ChatHistory[1].Content);
    }

    [Fact]
    public async Task ItParsesStandardizedPromptWhenServiceIsChatClientAsync()
    {
        using var fakeService = new FakeChatClient();
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<MEAI.IChatClient>((sp) => fakeService);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("""
            <message role="system">You are a helpful assistant.</message>
            <message role="user">How many 20 cents can I get from 1 dollar?</message>
            """);

        // Act + Assert
        await kernel.InvokeAsync(function);

        Assert.NotNull(fakeService.ChatMessages);
        Assert.Equal(2, fakeService.ChatMessages.Count);
        Assert.Equal("You are a helpful assistant.", fakeService.ChatMessages[0].Text);
        Assert.Equal("How many 20 cents can I get from 1 dollar?", fakeService.ChatMessages[1].Text);
    }

    [Fact]
    public async Task ItParsesStandardizedPromptWhenServiceIsStreamingChatCompletionAsync()
    {
        var fakeService = new FakeChatAsTextService();
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<ITextGenerationService>((sp) => fakeService);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("""
            <message role="system">You are a helpful assistant.</message>
            <message role="user">How many 20 cents can I get from 1 dollar?</message>
            """);

        // Act + Assert
        await foreach (var chunk in kernel.InvokeStreamingAsync(function))
        {
        }

        Assert.NotNull(fakeService.ChatHistory);
        Assert.Equal(2, fakeService.ChatHistory.Count);
        Assert.Equal("You are a helpful assistant.", fakeService.ChatHistory[0].Content);
        Assert.Equal("How many 20 cents can I get from 1 dollar?", fakeService.ChatHistory[1].Content);
    }

    [Fact]
    public async Task ItNotParsesStandardizedPromptWhenServiceIsOnlyTextCompletionAsync()
    {
        var mockService = new Mock<ITextGenerationService>();
        var mockResult = mockService.Setup(s => s.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync([new("something")]);

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<ITextGenerationService>((sp) => mockService.Object);
        Kernel kernel = builder.Build();

        var inputPrompt = """
            <message role="system">You are a helpful assistant.</message>
            <message role="user">How many 20 cents can I get from 1 dollar?</message>
            """;

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt(inputPrompt);

        // Act + Assert
        mockResult.Callback((string prompt, PromptExecutionSettings _, Kernel _, CancellationToken _) =>
        {
            Assert.NotNull(prompt);
            Assert.Equal(inputPrompt, prompt);
        });

        await kernel.InvokeAsync(function);
    }

    [Fact]
    public async Task ItNotParsesStandardizedPromptWhenStreamingWhenServiceIsOnlyTextCompletionAsync()
    {
        var mockService = new Mock<ITextGenerationService>();
        var mockResult = mockService.Setup(s => s.GetStreamingTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()))
            .Returns((new List<StreamingTextContent>() { new("something") }).ToAsyncEnumerable());

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<ITextGenerationService>((sp) => mockService.Object);
        Kernel kernel = builder.Build();

        var inputPrompt = """
            <message role="system">You are a helpful assistant.</message>
            <message role="user">How many 20 cents can I get from 1 dollar?</message>
            """;

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt(inputPrompt);

        // Act + Assert
        mockResult.Callback((string prompt, PromptExecutionSettings _, Kernel _, CancellationToken _) =>
        {
            Assert.NotNull(prompt);
            Assert.Equal(inputPrompt, prompt);
        });

        await foreach (var chunk in kernel.InvokeStreamingAsync(function))
        {
        }
    }

    [Fact]
    public async Task InvokeAsyncReturnsTheConnectorResultWhenInServiceIsOnlyTextCompletionAsync()
    {
        var mockService = new Mock<ITextGenerationService>();
        var mockResult = mockService.Setup(s => s.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync([new("something")]);

        KernelBuilder builder = new();
        builder.Services.AddTransient<ITextGenerationService>((sp) => mockService.Object);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Anything");

        var result = await kernel.InvokeAsync(function);

        Assert.Equal("something", result.GetValue<string>());
        Assert.Equal("something", result.GetValue<TextContent>()!.Text);
        Assert.Equal("something", result.GetValue<KernelContent>()!.ToString());
    }

    [Fact]
    public async Task InvokeAsyncReturnsTheConnectorChatResultWhenInServiceIsOnlyChatCompletionAsync()
    {
        var mockService = new Mock<IChatCompletionService>();
        var mockResult = mockService.Setup(s => s.GetChatMessageContentsAsync(It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync([new(AuthorRole.User, "something")]);

        KernelBuilder builder = new();
        builder.Services.AddTransient<IChatCompletionService>((sp) => mockService.Object);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Anything");

        var result = await kernel.InvokeAsync(function);

        Assert.Equal("something", result.GetValue<string>());
        Assert.Equal("something", result.GetValue<ChatMessageContent>()!.Content);
        Assert.Equal(AuthorRole.User, result.GetValue<ChatMessageContent>()!.Role);
        Assert.Equal("something", result.GetValue<KernelContent>()!.ToString());
    }

    [Fact]
    public async Task InvokeAsyncReturnsTheConnectorChatResultWhenInServiceIsOnlyChatClientAsync()
    {
        var customTestType = new CustomTestType();
        var fakeChatMessage = new MEAI.ChatMessage(MEAI.ChatRole.User, "something") { RawRepresentation = customTestType };
        var fakeChatResponse = new MEAI.ChatResponse(fakeChatMessage);
        Mock<MEAI.IChatClient> mockChatClient = new();
        mockChatClient.Setup(c => c.GetResponseAsync(It.IsAny<IList<MEAI.ChatMessage>>(), It.IsAny<MEAI.ChatOptions>(), It.IsAny<CancellationToken>())).ReturnsAsync(fakeChatResponse);
        mockChatClient.Setup(c => c.GetService(typeof(MEAI.ChatClientMetadata), It.IsAny<object?>())).Returns(new MEAI.ChatClientMetadata());

        using var chatClient = mockChatClient.Object;
        KernelBuilder builder = new();
        builder.Services.AddTransient<MEAI.IChatClient>((sp) => chatClient);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Anything");

        var result = await kernel.InvokeAsync(function);

        Assert.Equal("something", result.GetValue<string>());
        Assert.Equal("something", result.GetValue<MEAI.ChatMessage>()!.Text);
        Assert.Equal(MEAI.ChatRole.User, result.GetValue<MEAI.ChatMessage>()!.Role);
        Assert.Same(customTestType, result.GetValue<CustomTestType>()!);
        Assert.Equal("something", result.GetValue<MEAI.AIContent>()!.ToString());
        Assert.Equal("something", result.GetValue<MEAI.TextContent>()!.ToString());
    }

    [Fact]
    public async Task InvokeAsyncReturnsTheConnectorChatResultMessagesWhenInServiceIsOnlyChatClientAsync()
    {
        var firstMessageContent = "something 1";
        var lastMessageContent = "something 2";

        var customTestType = new CustomTestType();
        var fakeChatResponse = new MEAI.ChatResponse([
            new MEAI.ChatMessage(MEAI.ChatRole.User, firstMessageContent),
            new MEAI.ChatMessage(MEAI.ChatRole.Assistant, lastMessageContent) { RawRepresentation = customTestType }
        ]);

        Mock<MEAI.IChatClient> mockChatClient = new();
        mockChatClient.Setup(c => c.GetResponseAsync(It.IsAny<IList<MEAI.ChatMessage>>(), It.IsAny<MEAI.ChatOptions>(), It.IsAny<CancellationToken>())).ReturnsAsync(fakeChatResponse);
        mockChatClient.Setup(c => c.GetService(typeof(MEAI.ChatClientMetadata), It.IsAny<object?>())).Returns(new MEAI.ChatClientMetadata());

        using var chatClient = mockChatClient.Object;
        KernelBuilder builder = new();
        builder.Services.AddTransient<MEAI.IChatClient>((sp) => chatClient);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Anything");

        var result = await kernel.InvokeAsync(function);

        var response = result.GetValue<MEAI.ChatResponse>();
        Assert.NotNull(response);
        Assert.Collection(response.Messages,
            item1 =>
            {
                Assert.Equal(firstMessageContent, item1.Text); Assert.Equal(MEAI.ChatRole.User, item1.Role);
            },
            item2 =>
            {
                Assert.Equal(lastMessageContent, item2.Text); Assert.Equal(MEAI.ChatRole.Assistant, item2.Role);
            });

        // Other specific types will be checked against the first choice and last message
        Assert.Equal(lastMessageContent, result.GetValue<string>());
        Assert.Equal(lastMessageContent, result.GetValue<MEAI.ChatMessage>()!.Text);
        Assert.Equal(MEAI.ChatRole.Assistant, result.GetValue<MEAI.ChatMessage>()!.Role);
        Assert.Same(customTestType, result.GetValue<CustomTestType>()!);
        Assert.Equal(lastMessageContent, result.GetValue<MEAI.TextContent>()!.ToString());
        Assert.Equal(lastMessageContent, result.GetValue<MEAI.AIContent>()!.ToString());
    }

    [Fact]
    public async Task InvokeAsyncReturnsTheConnectorChatResultWhenInServiceIsChatAndTextCompletionAsync()
    {
        var fakeService = new FakeChatAsTextService();
        KernelBuilder builder = new();
        builder.Services.AddTransient<ITextGenerationService>((sp) => fakeService);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Anything");

        var result = await kernel.InvokeAsync(function);

        Assert.Equal("Something", result.GetValue<string>());
        Assert.Equal("Something", result.GetValue<ChatMessageContent>()!.Content);
        Assert.Equal(AuthorRole.Assistant, result.GetValue<ChatMessageContent>()!.Role);
        Assert.Equal("Something", result.GetValue<KernelContent>()!.ToString());
    }

    [Fact]
    public async Task InvokeAsyncOfTGivesBackTheExpectedResultTypeFromTheConnectorWhenStreamingWhenServiceIsOnlyTextCompletionAsync()
    {
        var expectedContent = new StreamingTextContent("something");
        var mockService = new Mock<ITextGenerationService>();
        var mockResult = mockService.Setup(s => s.GetStreamingTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()))
            .Returns((new List<StreamingTextContent>() { expectedContent }).ToAsyncEnumerable());

        KernelBuilder builder = new();
        builder.Services.AddTransient<ITextGenerationService>((sp) => mockService.Object);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Anything");

        await foreach (var chunk in kernel.InvokeStreamingAsync<StreamingKernelContent>(function))
        {
            Assert.Equal(expectedContent, chunk);
        }

        await foreach (var chunk in kernel.InvokeStreamingAsync<StreamingTextContent>(function))
        {
            Assert.Equal(expectedContent, chunk);
        }
    }

    [Fact]
    public async Task InvokeAsyncOfTGivesBackTheExpectedResultTypeFromTheConnectorWhenStreamingWhenerviceIsOnlyChatCompletionAsync()
    {
        var expectedContent = new StreamingChatMessageContent(AuthorRole.Assistant, "Something");
        var mockService = new Mock<IChatCompletionService>();
        var mockResult = mockService.Setup(s => s.GetStreamingChatMessageContentsAsync(It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()))
            .Returns((new List<StreamingChatMessageContent>() { expectedContent }).ToAsyncEnumerable());

        KernelBuilder builder = new();
        builder.Services.AddTransient<IChatCompletionService>((sp) => mockService.Object);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Anything");

        await foreach (var chunk in kernel.InvokeStreamingAsync<StreamingKernelContent>(function))
        {
            Assert.Equal(expectedContent, chunk);
            Assert.Equal("Something", chunk.ToString());
        }

        await foreach (var chunk in kernel.InvokeStreamingAsync<StreamingChatMessageContent>(function))
        {
            Assert.Equal(expectedContent, chunk);
            Assert.Equal("Something", chunk.Content);
            Assert.Equal(AuthorRole.Assistant, chunk.Role);
        }
    }

    [Fact]
    public async Task InvokeAsyncOfTGivesBackTheExpectedResultTypeFromTheConnectorWhenStreamingWhenServiceIsTextAndChatCompletionAsync()
    {
        var fakeService = new FakeChatAsTextService();
        KernelBuilder builder = new();
        builder.Services.AddTransient<ITextGenerationService>((sp) => fakeService);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Anything");

        await foreach (var chunk in kernel.InvokeStreamingAsync<StreamingKernelContent>(function))
        {
            Assert.Equal("Something", chunk.ToString());
        }

        await foreach (var chunk in kernel.InvokeStreamingAsync<StreamingChatMessageContent>(function))
        {
            Assert.Equal(AuthorRole.Assistant, chunk.Role);
            Assert.Equal("Something", chunk.Content);
        }
    }

    [Fact]
    public async Task InvokeAsyncUsesPromptExecutionSettingsAsync()
    {
        // Arrange
        var mockTextContent = new TextContent("Result");
        var mockTextCompletion = new Mock<ITextGenerationService>();
        mockTextCompletion.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([mockTextContent]);
        KernelBuilder builder = new();
        builder.Services.AddTransient<ITextGenerationService>((sp) => mockTextCompletion.Object);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Anything", new OpenAIPromptExecutionSettings { MaxTokens = 1000 });

        // Act
        var result = await kernel.InvokeAsync(function);

        // Assert
        Assert.Equal("Result", result.GetValue<string>());
        mockTextCompletion.Verify(m => m.GetTextContentsAsync("Anything", It.Is<OpenAIPromptExecutionSettings>(settings => settings.MaxTokens == 1000), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task InvokeAsyncUsesKernelArgumentsExecutionSettingsAsync()
    {
        // Arrange
        var mockTextContent = new TextContent("Result");
        var mockTextCompletion = new Mock<ITextGenerationService>();
        mockTextCompletion.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([mockTextContent]);
        KernelBuilder builder = new();
        builder.Services.AddTransient<ITextGenerationService>((sp) => mockTextCompletion.Object);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Anything", new OpenAIPromptExecutionSettings { MaxTokens = 1000 });

        // Act
        var result = await kernel.InvokeAsync(function, new KernelArguments(new OpenAIPromptExecutionSettings { MaxTokens = 2000 }));

        // Assert
        Assert.Equal("Result", result.GetValue<string>());
        mockTextCompletion.Verify(m => m.GetTextContentsAsync("Anything", It.Is<OpenAIPromptExecutionSettings>(settings => settings.MaxTokens == 2000), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task InvokeAsyncWithServiceIdUsesKernelArgumentsExecutionSettingsAsync()
    {
        // Arrange
        var mockTextContent = new TextContent("Result");
        var mockTextCompletion = new Mock<ITextGenerationService>();
        mockTextCompletion.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([mockTextContent]);
        KernelBuilder builder = new();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", mockTextCompletion.Object);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Anything", new OpenAIPromptExecutionSettings { MaxTokens = 1000 });

        // Act
        var result = await kernel.InvokeAsync(function, new KernelArguments(new OpenAIPromptExecutionSettings { MaxTokens = 2000 }));

        // Assert
        Assert.Equal("Result", result.GetValue<string>());
        mockTextCompletion.Verify(m => m.GetTextContentsAsync("Anything", It.Is<OpenAIPromptExecutionSettings>(settings => settings.MaxTokens == 2000), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task InvokeAsyncWithMultipleServicesUsesKernelArgumentsExecutionSettingsAsync()
    {
        // Arrange
        var mockTextContent1 = new TextContent("Result1");
        var mockTextCompletion1 = new Mock<ITextGenerationService>();
        mockTextCompletion1.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([mockTextContent1]);
        var mockTextContent2 = new TextContent("Result2");
        var mockTextCompletion2 = new Mock<ITextGenerationService>();
        mockTextCompletion2.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([mockTextContent2]);

        KernelBuilder builder = new();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", mockTextCompletion1.Object);
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service2", mockTextCompletion2.Object);
        Kernel kernel = builder.Build();

        KernelFunction function1 = KernelFunctionFactory.CreateFromPrompt(new PromptTemplateConfig { Template = "Prompt1", ExecutionSettings = new() { ["service1"] = new OpenAIPromptExecutionSettings { MaxTokens = 1000 } } });
        KernelFunction function2 = KernelFunctionFactory.CreateFromPrompt(new PromptTemplateConfig { Template = "Prompt2", ExecutionSettings = new() { ["service2"] = new OpenAIPromptExecutionSettings { MaxTokens = 2000 } } });

        // Act
        var result1 = await kernel.InvokeAsync(function1);
        var result2 = await kernel.InvokeAsync(function2);

        // Assert
        Assert.Equal("Result1", result1.GetValue<string>());
        mockTextCompletion1.Verify(m => m.GetTextContentsAsync("Prompt1", It.Is<OpenAIPromptExecutionSettings>(settings => settings.MaxTokens == 1000), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
        Assert.Equal("Result2", result2.GetValue<string>());
        mockTextCompletion2.Verify(m => m.GetTextContentsAsync("Prompt2", It.Is<OpenAIPromptExecutionSettings>(settings => settings.MaxTokens == 2000), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task InvokeAsyncWithMultipleServicesUsesServiceFromKernelArgumentsExecutionSettingsAsync()
    {
        // Arrange
        var mockTextContent1 = new TextContent("Result1");
        var mockTextCompletion1 = new Mock<ITextGenerationService>();
        mockTextCompletion1.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([mockTextContent1]);
        var mockTextContent2 = new TextContent("Result2");
        var mockTextCompletion2 = new Mock<ITextGenerationService>();
        mockTextCompletion2.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([mockTextContent2]);

        KernelBuilder builder = new();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", mockTextCompletion1.Object);
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service2", mockTextCompletion2.Object);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("Prompt");

        // Act
        KernelArguments arguments1 = [];
        arguments1.ExecutionSettings = new Dictionary<string, PromptExecutionSettings>()
        {
            { "service1", new OpenAIPromptExecutionSettings { MaxTokens = 1000 } }
        };
        var result1 = await kernel.InvokeAsync(function, arguments1);

        KernelArguments arguments2 = [];
        arguments2.ExecutionSettings = new Dictionary<string, PromptExecutionSettings>()
        {
            { "service2", new OpenAIPromptExecutionSettings { MaxTokens = 2000 } }
        };
        var result2 = await kernel.InvokeAsync(function, arguments2);

        // Assert
        Assert.Equal("Result1", result1.GetValue<string>());
        mockTextCompletion1.Verify(m => m.GetTextContentsAsync("Prompt", It.Is<OpenAIPromptExecutionSettings>(settings => settings.MaxTokens == 1000), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
        Assert.Equal("Result2", result2.GetValue<string>());
        mockTextCompletion2.Verify(m => m.GetTextContentsAsync("Prompt", It.Is<OpenAIPromptExecutionSettings>(settings => settings.MaxTokens == 2000), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task InvokeAsyncWithMultipleServicesUsesKernelArgumentsExecutionSettingsOverrideAsync()
    {
        // Arrange
        var mockTextContent1 = new TextContent("Result1");
        var mockTextCompletion1 = new Mock<ITextGenerationService>();
        mockTextCompletion1.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([mockTextContent1]);
        var mockTextContent2 = new TextContent("Result2");
        var mockTextCompletion2 = new Mock<ITextGenerationService>();
        mockTextCompletion2.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([mockTextContent2]);

        KernelBuilder builder = new();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", mockTextCompletion1.Object);
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service2", mockTextCompletion2.Object);
        Kernel kernel = builder.Build();

        KernelFunction function1 = KernelFunctionFactory.CreateFromPrompt(new PromptTemplateConfig { Template = "Prompt1", ExecutionSettings = new() { ["service1"] = new OpenAIPromptExecutionSettings { MaxTokens = 1000 } } });
        KernelFunction function2 = KernelFunctionFactory.CreateFromPrompt(new PromptTemplateConfig { Template = "Prompt2", ExecutionSettings = new() { ["service2"] = new OpenAIPromptExecutionSettings { MaxTokens = 2000 } } });

        // Act
        KernelArguments arguments1 = [];
        arguments1.ExecutionSettings = new Dictionary<string, PromptExecutionSettings>()
        {
            { "service2", new OpenAIPromptExecutionSettings { MaxTokens = 2000 } }
        };
        var result1 = await kernel.InvokeAsync(function1, arguments1);

        KernelArguments arguments2 = [];
        arguments2.ExecutionSettings = new Dictionary<string, PromptExecutionSettings>()
        {
            { "service1", new OpenAIPromptExecutionSettings { MaxTokens = 1000 } }
        };
        var result2 = await kernel.InvokeAsync(function2, arguments2);

        // Assert
        Assert.Equal("Result2", result1.GetValue<string>());
        mockTextCompletion2.Verify(m => m.GetTextContentsAsync("Prompt1", It.Is<OpenAIPromptExecutionSettings>(settings => settings.MaxTokens == 2000), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
        Assert.Equal("Result1", result2.GetValue<string>());
        mockTextCompletion1.Verify(m => m.GetTextContentsAsync("Prompt2", It.Is<OpenAIPromptExecutionSettings>(settings => settings.MaxTokens == 1000), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public async Task InvokeAsyncWithNestedPromptsSelectsCorrectServiceAsync()
    {
        // Arrange
        var mockTextContent1 = new TextContent("Result1");
        var mockTextCompletion1 = new Mock<ITextGenerationService>();
        mockTextCompletion1.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([mockTextContent1]);
        var mockTextContent2 = new TextContent("Result2");
        var mockTextCompletion2 = new Mock<ITextGenerationService>();
        mockTextCompletion2.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([mockTextContent2]);

        KernelBuilder builder = new();
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service1", mockTextCompletion1.Object);
        builder.Services.AddKeyedSingleton<ITextGenerationService>("service2", mockTextCompletion2.Object);
        Kernel kernel = builder.Build();

        KernelFunction function1 = KernelFunctionFactory.CreateFromPrompt(new PromptTemplateConfig { Name = "Prompt1", Template = "Prompt1", ExecutionSettings = new() { ["service1"] = new OpenAIPromptExecutionSettings { MaxTokens = 1000 } } });
        KernelFunction function2 = KernelFunctionFactory.CreateFromPrompt(new PromptTemplateConfig { Name = "Prompt2", Template = "Prompt2 {{MyPrompts.Prompt1}}", ExecutionSettings = new() { ["service2"] = new OpenAIPromptExecutionSettings { MaxTokens = 2000 } } });

        kernel.ImportPluginFromFunctions("MyPrompts", [function1, function2]);

        // Act
        var result = await kernel.InvokeAsync(function2);

        // Assert
        Assert.Equal("Result2", result.GetValue<string>());
        mockTextCompletion1.Verify(m => m.GetTextContentsAsync("Prompt1", It.Is<OpenAIPromptExecutionSettings>(settings => settings.MaxTokens == 1000), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
        mockTextCompletion2.Verify(m => m.GetTextContentsAsync("Prompt2 Result1", It.Is<OpenAIPromptExecutionSettings>(settings => settings.MaxTokens == 2000), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Theory]
    [InlineData(KernelInvocationType.InvokePrompt)]
    [InlineData(KernelInvocationType.InvokePromptStreaming)]
    [InlineData(KernelInvocationType.InvokeFunction)]
    [InlineData(KernelInvocationType.InvokeFunctionStreaming)]
    public async Task ItUsesPromptAsUserMessageAsync(KernelInvocationType invocationType)
    {
        // Arrange
        const string Prompt = "Test prompt as user message";

        var fakeService = new FakeChatAsTextService();
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<IChatCompletionService>((sp) => fakeService);
        Kernel kernel = builder.Build();

        var function = KernelFunctionFactory.CreateFromPrompt(Prompt);

        // Act
        switch (invocationType)
        {
            case KernelInvocationType.InvokePrompt:
                await kernel.InvokePromptAsync(Prompt);
                break;
            case KernelInvocationType.InvokePromptStreaming:
                await foreach (var result in kernel.InvokePromptStreamingAsync(Prompt)) { }
                break;
            case KernelInvocationType.InvokeFunction:
                await kernel.InvokeAsync(function);
                break;
            case KernelInvocationType.InvokeFunctionStreaming:
                await foreach (var result in kernel.InvokeStreamingAsync(function)) { }
                break;
        }

        // Assert
        Assert.NotNull(fakeService.ChatHistory);
        Assert.Single(fakeService.ChatHistory);

        var messageContent = fakeService.ChatHistory[0];

        Assert.Equal(AuthorRole.User, messageContent.Role);
        Assert.Equal("Test prompt as user message", messageContent.Content);
    }

    [Theory]
    [InlineData("semantic-kernel", "This is my prompt {{$input}}")]
    [InlineData("handlebars", "This is my prompt {{input}}")]
    public async Task ItUsesPromptWithEchoPromptTemplateFactoryAsync(string templateFormat, string template)
    {
        // Arrange
        var mockTextGeneration = new Mock<ITextGenerationService>();
        var fakeTextContent = new TextContent(template);

        mockTextGeneration.Setup(c => c.GetTextContentsAsync(It.Is<string>(p => p.Equals(template, StringComparison.Ordinal)), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([fakeTextContent]);

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddKeyedSingleton("x", mockTextGeneration.Object);
        Kernel kernel = builder.Build();

        var promptConfig = new PromptTemplateConfig(template) { TemplateFormat = templateFormat };
        var func = kernel.CreateFunctionFromPrompt(promptConfig, promptTemplateFactory: new EchoPromptTemplateFactory());
        var args = new KernelArguments();
        args["input"] = "Some Input";

        // Act
        var result = await kernel.InvokeAsync(func, args);

        // Assert
        mockTextGeneration.Verify(a => a.GetTextContentsAsync(template, It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Once());
        Assert.Equal(template, result.GetValue<string>());
    }

    [Fact]
    public async Task InvokePromptAsyncWithTextGenerationReturnsSingleResultAsync()
    {
        // Arrange
        var expectedTextContent = new TextContent("text", "model-id", metadata: new Dictionary<string, object?> { { "key", "value" } });
        var mockTextGenerationService = this.GetMockTextGenerationService(textContents: [expectedTextContent]);

        KernelBuilder builder = new();
        builder.Services.AddTransient<ITextGenerationService>((sp) => mockTextGenerationService.Object);
        Kernel kernel = builder.Build();

        // Act
        var result = await kernel.InvokePromptAsync("Prompt");

        // Assert
        Assert.Equal("text", result.GetValue<string>());
        Assert.Equal("text", result.GetValue<KernelContent>()!.ToString());

        var actualTextContent = result.GetValue<TextContent>();

        Assert.NotNull(actualTextContent);
        Assert.Equal(result.Metadata, actualTextContent.Metadata);

        Assert.Equal(expectedTextContent.ModelId, actualTextContent.ModelId);
        Assert.Equal(expectedTextContent.Text, actualTextContent.Text);
        Assert.Equal(expectedTextContent.Metadata, actualTextContent.Metadata);
    }

    [Fact]
    public async Task InvokePromptAsyncWithTextGenerationReturnsMultipleResultsAsync()
    {
        // Arrange
        List<TextContent> expectedTextContents =
        [
            new TextContent("text1", "model-id", metadata: new Dictionary<string, object?> { { "key1", "value1" } }),
            new TextContent("text2", "model-id", metadata: new Dictionary<string, object?> { { "key2", "value2" } }),
        ];

        var mockTextGenerationService = this.GetMockTextGenerationService(textContents: expectedTextContents);

        KernelBuilder builder = new();
        builder.Services.AddTransient<ITextGenerationService>((sp) => mockTextGenerationService.Object);
        Kernel kernel = builder.Build();

        // Act
        var result = await kernel.InvokePromptAsync("Prompt");

        // Assert
        Assert.Throws<InvalidCastException>(() => result.GetValue<string>());
        Assert.Throws<InvalidCastException>(() => result.GetValue<KernelContent>());

        var actualTextContents = result.GetValue<IReadOnlyList<TextContent>>();

        Assert.NotNull(actualTextContents);
        Assert.Null(result.Metadata);

        Assert.Equal(expectedTextContents.Count, actualTextContents.Count);

        for (var i = 0; i < expectedTextContents.Count; i++)
        {
            Assert.Equal(expectedTextContents[i].ModelId, actualTextContents[i].ModelId);
            Assert.Equal(expectedTextContents[i].Text, actualTextContents[i].Text);
            Assert.Equal(expectedTextContents[i].Metadata, actualTextContents[i].Metadata);
        }
    }

    [Fact]
    public async Task InvokePromptAsyncWithChatCompletionReturnsSingleResultAsync()
    {
        // Arrange
        var expectedChatMessageContent = new ChatMessageContent(AuthorRole.Assistant, "chat-message", "model-id", new Dictionary<string, object?> { { "key", "value" } });
        var mockChatCompletionService = this.GetMockChatCompletionService(chatMessageContents: [expectedChatMessageContent]);

        KernelBuilder builder = new();
        builder.Services.AddTransient<IChatCompletionService>((sp) => mockChatCompletionService.Object);
        Kernel kernel = builder.Build();

        // Act
        var result = await kernel.InvokePromptAsync("Prompt");

        // Assert
        Assert.Equal("chat-message", result.GetValue<string>());
        Assert.Equal("chat-message", result.GetValue<KernelContent>()!.ToString());

        var actualChatMessageContent = result.GetValue<ChatMessageContent>();

        Assert.NotNull(actualChatMessageContent);
        Assert.Equal(result.Metadata, expectedChatMessageContent.Metadata);

        Assert.Equal(expectedChatMessageContent.ModelId, actualChatMessageContent.ModelId);
        Assert.Equal(expectedChatMessageContent.Role, actualChatMessageContent.Role);
        Assert.Equal(expectedChatMessageContent.Content, actualChatMessageContent.Content);
        Assert.Equal(expectedChatMessageContent.Metadata, actualChatMessageContent.Metadata);
    }

    [Fact]
    public async Task InvokePromptAsyncWithChatCompletionReturnsMultipleResultsAsync()
    {
        // Arrange
        List<ChatMessageContent> expectedChatMessageContents =
        [
            new ChatMessageContent(AuthorRole.Assistant, "chat-message1", "model-id", new Dictionary<string, object?> { { "key1", "value1" } }),
            new ChatMessageContent(AuthorRole.Assistant, "chat-message2", "model-id", new Dictionary<string, object?> { { "key2", "value2" } })
        ];

        var mockChatCompletionService = this.GetMockChatCompletionService(chatMessageContents: expectedChatMessageContents);

        KernelBuilder builder = new();
        builder.Services.AddTransient<IChatCompletionService>((sp) => mockChatCompletionService.Object);
        Kernel kernel = builder.Build();

        // Act
        var result = await kernel.InvokePromptAsync("Prompt");

        // Assert
        Assert.Throws<InvalidCastException>(() => result.GetValue<string>());
        Assert.Throws<InvalidCastException>(() => result.GetValue<KernelContent>());

        var actualChatMessageContents = result.GetValue<IReadOnlyList<ChatMessageContent>>();

        Assert.NotNull(actualChatMessageContents);
        Assert.Null(result.Metadata);

        Assert.Equal(expectedChatMessageContents.Count, actualChatMessageContents.Count);

        for (var i = 0; i < expectedChatMessageContents.Count; i++)
        {
            Assert.Equal(expectedChatMessageContents[i].ModelId, actualChatMessageContents[i].ModelId);
            Assert.Equal(expectedChatMessageContents[i].Role, actualChatMessageContents[i].Role);
            Assert.Equal(expectedChatMessageContents[i].Content, actualChatMessageContents[i].Content);
            Assert.Equal(expectedChatMessageContents[i].Metadata, actualChatMessageContents[i].Metadata);
        }
    }

    [Fact]
    public async Task InvokePromptAsyncWithChatCompletionPropagatesTooManyRequestsAsync()
    {
        // Arrange
        using var messageHandlerStub = new HttpMessageHandlerStub();
        using var response = new HttpResponseMessage(System.Net.HttpStatusCode.TooManyRequests);
        messageHandlerStub.ResponseToReturn = response;
        using var httpClient = new HttpClient(messageHandlerStub, false);
        var chatCompletion = new OpenAIChatCompletionService(modelId: "any", apiKey: "any", httpClient: httpClient);

        KernelBuilder builder = new();
        builder.Services.AddTransient<IChatCompletionService>((sp) => chatCompletion);
        Kernel kernel = builder.Build();

        // Act
        var exception = await Assert.ThrowsAsync<HttpOperationException>(async () => await kernel.InvokePromptAsync("Prompt"));

        // Assert
        Assert.Equal(HttpStatusCode.TooManyRequests, exception.StatusCode);
    }

    [Fact]
    public async Task InvokePromptAsyncWithPromptFunctionInTemplateAndSingleResultAsync()
    {
        // Arrange
        var expectedChatMessageContent = new ChatMessageContent(AuthorRole.Assistant, "chat-message", "model-id", new Dictionary<string, object?> { { "key", "value" } });
        var mockChatCompletionService = this.GetMockChatCompletionService(chatMessageContents: [expectedChatMessageContent]);

        KernelBuilder builder = new();
        builder.Services.AddTransient<IChatCompletionService>((sp) => mockChatCompletionService.Object);
        Kernel kernel = builder.Build();

        var innerFunction = KernelFunctionFactory.CreateFromPrompt("Prompt", functionName: "GetData");
        var plugin = KernelPluginFactory.CreateFromFunctions("MyPlugin", [innerFunction]);

        kernel.Plugins.Add(plugin);

        // Act
        var result = await kernel.InvokePromptAsync("Data: {{MyPlugin.GetData}}");

        // Assert
        Assert.True(mockChatCompletionService.Invocations is { Count: 2 });

        var lastInvocation = mockChatCompletionService.Invocations[^1];
        var lastInvocationChatHistory = lastInvocation!.Arguments[0] as ChatHistory;

        Assert.NotNull(lastInvocationChatHistory);
        Assert.Equal("Data: chat-message", lastInvocationChatHistory[0].Content);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public void ItThrowsExceptionNoTemplateFormatIsProvided(JsonSerializerOptions? jsos)
    {
        // Act
        Assert.Throws<ArgumentException>(
            () =>
            jsos is not null ?
                KernelFunctionFromPrompt.Create("prompt-template", jsonSerializerOptions: jsos, templateFormat: null, promptTemplateFactory: new EchoPromptTemplateFactory()) :
                KernelFunctionFromPrompt.Create("prompt-template", templateFormat: null, promptTemplateFactory: new EchoPromptTemplateFactory())
        );
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItCanBeCloned(JsonSerializerOptions? jsos)
    {
        // Arrange
        var mockService = new Mock<IChatCompletionService>();
        mockService
            .Setup(s => s.GetChatMessageContentsAsync(It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings?>(), It.IsAny<Kernel?>(), It.IsAny<CancellationToken>()))
            .Returns((ChatHistory ch, PromptExecutionSettings? _, Kernel? _, CancellationToken _) => Task.FromResult((IReadOnlyList<ChatMessageContent>)[new(AuthorRole.Assistant, ch.First().Content)]));

        var builder = new KernelBuilder();
        builder.Services.AddSingleton<IChatCompletionService>(mockService.Object);

        var kernel = builder.Build();

        KernelFunction function = jsos is not null ?
            function = KernelFunctionFromPrompt.Create("Prompt with {{$A}} variable", jsonSerializerOptions: jsos) :
            function = KernelFunctionFromPrompt.Create("Prompt with {{$A}} variable");

        // Act
        function = function.Clone("new-plugin-name");

        // Assert plugin name
        Assert.Equal("new-plugin-name", function.Metadata.PluginName);

        // Assert schema
        Assert.NotEmpty(function.Metadata.Parameters);
        Assert.NotNull(function.Metadata.Parameters[0].Schema);
        Assert.Equal("{\"type\":\"string\"}", function.Metadata.Parameters[0].Schema!.ToString());

        Assert.NotNull(function.Metadata.ReturnParameter);
        Assert.Null(function.Metadata.ReturnParameter.Schema);

        // Assert invocation
        var invokeResult = await function.InvokeAsync(kernel, new() { ["A"] = "a" });
        var result = invokeResult?.GetValue<string>();
        Assert.Equal("Prompt with a variable", result);
    }

    [Fact]
    public async Task ItCanRetrieveDirectMEAIChatMessageUpdatesAsync()
    {
        using var fakeService = new FakeChatClient()
        {
            GetStreamingResponseResult = [
                new MEAI.ChatResponseUpdate(MEAI.ChatRole.Assistant, "Hi! How can "),
                new MEAI.ChatResponseUpdate(role: null, content: "I assist you today?")
            ]
        };

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<MEAI.IChatClient>((sp) => fakeService);
        Kernel kernel = builder.Build();

        // Act + Assert
        var updateIndex = 0;
        await foreach (var update in kernel.InvokeStreamingAsync<MEAI.ChatResponseUpdate>(KernelFunctionFromPrompt.Create("Prompt with {{$A}} variable")))
        {
            Assert.Same(fakeService.GetStreamingResponseResult![updateIndex], update);
            Assert.Equal(fakeService.GetStreamingResponseResult![updateIndex].Text, update.Text);

            updateIndex++;
        }

        Assert.Equal(updateIndex, fakeService.GetStreamingResponseResult.Count);
    }

    [Fact]
    public async Task ItCanRetrieveDirectMEAITextContentAsync()
    {
        using var fakeService = new FakeChatClient()
        {
            GetStreamingResponseResult = [
                new MEAI.ChatResponseUpdate(MEAI.ChatRole.Assistant, "Hi! How can "),
                new MEAI.ChatResponseUpdate(role: null, content: "I assist you today?")
            ]
        };

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<MEAI.IChatClient>((sp) => fakeService);
        Kernel kernel = builder.Build();

        // Act + Assert
        var updateIndex = 0;
        await foreach (var update in kernel.InvokeStreamingAsync<MEAI.TextContent>(KernelFunctionFromPrompt.Create("Prompt with {{$A}} variable")))
        {
            Assert.Same(fakeService.GetStreamingResponseResult![updateIndex].Contents[0], update);

            updateIndex++;
        }

        Assert.Equal(updateIndex, fakeService.GetStreamingResponseResult.Count);
    }

    [Fact]
    public async Task ItCanRetrieveDirectMEAIStringAsync()
    {
        using var fakeService = new FakeChatClient()
        {
            GetStreamingResponseResult = [
                new MEAI.ChatResponseUpdate(MEAI.ChatRole.Assistant, "Hi! How can "),
                new MEAI.ChatResponseUpdate(role: null, content: "I assist you today?")
            ]
        };

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<MEAI.IChatClient>((sp) => fakeService);
        Kernel kernel = builder.Build();

        // Act + Assert
        var updateIndex = 0;
        await foreach (var update in kernel.InvokeStreamingAsync<string>(KernelFunctionFromPrompt.Create("Prompt with {{$A}} variable")))
        {
            Assert.Equal(fakeService.GetStreamingResponseResult![updateIndex].Text, update);

            updateIndex++;
        }

        Assert.Equal(updateIndex, fakeService.GetStreamingResponseResult.Count);
    }

    [Fact]
    public async Task ItCanRetrieveDirectMEAIRawRepresentationAsync()
    {
        var rawRepresentation = OpenAI.Chat.OpenAIChatModelFactory.StreamingChatCompletionUpdate(contentUpdate: new OpenAI.Chat.ChatMessageContent("Hi!"));
        using var fakeService = new FakeChatClient()
        {
            GetStreamingResponseResult = [
                new MEAI.ChatResponseUpdate(role: MEAI.ChatRole.Assistant, content: "Hi! How can ") { RawRepresentation = rawRepresentation },
                new MEAI.ChatResponseUpdate(role: null, content: "I assist you today?") { RawRepresentation = rawRepresentation }
            ]
        };

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<MEAI.IChatClient>((sp) => fakeService);
        Kernel kernel = builder.Build();

        // Act + Assert
        var updateIndex = 0;
        await foreach (var update in kernel.InvokeStreamingAsync<OpenAI.Chat.StreamingChatCompletionUpdate>(KernelFunctionFromPrompt.Create("Prompt with {{$A}} variable")))
        {
            Assert.Same(fakeService.GetStreamingResponseResult![updateIndex].RawRepresentation, update);

            updateIndex++;
        }

        Assert.Equal(updateIndex, fakeService.GetStreamingResponseResult.Count);
    }

    [Fact]
    public async Task ItCanRetrieveDirectMEAIContentListAsync()
    {
        var rawRepresentation = OpenAI.Chat.OpenAIChatModelFactory.StreamingChatCompletionUpdate(contentUpdate: new OpenAI.Chat.ChatMessageContent("Hi!"));
        using var fakeService = new FakeChatClient()
        {
            GetStreamingResponseResult = [
                new MEAI.ChatResponseUpdate(role: MEAI.ChatRole.Assistant, content: "Hi! How can ") { RawRepresentation = rawRepresentation },
                new MEAI.ChatResponseUpdate(role: null, content: "I assist you today?") { RawRepresentation = rawRepresentation }
            ]
        };

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<MEAI.IChatClient>((sp) => fakeService);
        Kernel kernel = builder.Build();

        // Act + Assert
        var updateIndex = 0;
        await foreach (var update in kernel.InvokeStreamingAsync<IList<MEAI.AIContent>>(KernelFunctionFromPrompt.Create("Prompt with {{$A}} variable")))
        {
            Assert.Same(fakeService.GetStreamingResponseResult![updateIndex].Contents, update);

            updateIndex++;
        }

        Assert.Equal(updateIndex, fakeService.GetStreamingResponseResult.Count);
    }

    [Fact]
    public async Task ItConvertsFromMEAIChatMessageUpdateToSKStreamingChatMessageContentAsync()
    {
        var rawRepresentation = new { test = "a" };
        using var fakeService = new FakeChatClient()
        {
            GetStreamingResponseResult = [
                new MEAI.ChatResponseUpdate(MEAI.ChatRole.Assistant, "Hi! How can ") { RawRepresentation = rawRepresentation },
                new MEAI.ChatResponseUpdate(role: null, content: "I assist you today?") { RawRepresentation = rawRepresentation }
            ]
        };

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<MEAI.IChatClient>((sp) => fakeService);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("""
            <message role="system">You are a helpful assistant.</message>
            <message role="user">How many 20 cents can I get from 1 dollar?</message>
            """);

        // Act + Assert
        var updateIndex = 0;
        await foreach (var update in kernel.InvokeStreamingAsync<StreamingChatMessageContent>(function))
        {
            Assert.Equal(fakeService.GetStreamingResponseResult![updateIndex].Text, update.Content);
            Assert.Same(fakeService.GetStreamingResponseResult![updateIndex].RawRepresentation, update.InnerContent);
            updateIndex++;
        }

        Assert.Equal(updateIndex, fakeService.GetStreamingResponseResult.Count);
    }

    [Fact]
    public async Task ItConvertsFromMEAIChatMessageUpdateToSKStreamingContentAsync()
    {
        var rawRepresentation = new { test = "a" };
        using var fakeService = new FakeChatClient()
        {
            GetStreamingResponseResult = [
                new MEAI.ChatResponseUpdate(MEAI.ChatRole.Assistant, "Hi! How can ") { RawRepresentation = rawRepresentation },
                new MEAI.ChatResponseUpdate(role: null, content: "I assist you today?") { RawRepresentation = rawRepresentation }
            ]
        };

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<MEAI.IChatClient>((sp) => fakeService);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("""
            <message role="system">You are a helpful assistant.</message>
            <message role="user">How many 20 cents can I get from 1 dollar?</message>
            """);

        // Act + Assert
        var updateIndex = 0;
        await foreach (var update in kernel.InvokeStreamingAsync<StreamingKernelContent>(function))
        {
            var streamingChatContent = Assert.IsType<StreamingChatMessageContent>(update);
            Assert.Same(fakeService.GetStreamingResponseResult![updateIndex].RawRepresentation, update.InnerContent);

            Assert.Equal(fakeService.GetStreamingResponseResult![updateIndex].Text, streamingChatContent.Content);
            updateIndex++;
        }

        Assert.Equal(updateIndex, fakeService.GetStreamingResponseResult.Count);
    }

    [Fact]
    public async Task ItConvertsFromSKStreamingChatMessageContentToMEAIChatResponseUpdate()
    {
        var innerContent = new { test = "a" };
        var fakeService = new FakeChatCompletionService()
        {
            GetStreamingChatMessageContentsResult = [
                new StreamingChatMessageContent(AuthorRole.Assistant, "Hi! How can ") { InnerContent = innerContent },
                new StreamingChatMessageContent(null, "I assist you today?") { InnerContent = innerContent }
            ]
        };

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<IChatCompletionService>((sp) => fakeService);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("""
            <message role="system">You are a helpful assistant.</message>
            <message role="user">How many 20 cents can I get from 1 dollar?</message>
            """);

        // Act + Assert
        var updateIndex = 0;
        await foreach (var update in kernel.InvokeStreamingAsync<MEAI.ChatResponseUpdate>(function))
        {
            Assert.Same(fakeService.GetStreamingChatMessageContentsResult![updateIndex].InnerContent, update.RawRepresentation);

            Assert.Equal(fakeService.GetStreamingChatMessageContentsResult![updateIndex].Content, update.Text);
            updateIndex++;
        }

        Assert.Equal(updateIndex, fakeService.GetStreamingChatMessageContentsResult.Count);
    }

    [Fact]
    public async Task ItConvertsFromSKStreamingChatMessageContentToStringAsync()
    {
        var innerContent = new { test = "a" };
        var fakeService = new FakeChatCompletionService()
        {
            GetStreamingChatMessageContentsResult = [
                new StreamingChatMessageContent(AuthorRole.Assistant, "Hi! How can ") { InnerContent = innerContent },
                new StreamingChatMessageContent(null, "I assist you today?") { InnerContent = innerContent }
            ]
        };

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<IChatCompletionService>((sp) => fakeService);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("""
            <message role="system">You are a helpful assistant.</message>
            <message role="user">How many 20 cents can I get from 1 dollar?</message>
            """);

        // Act + Assert
        var updateIndex = 0;
        await foreach (var update in kernel.InvokeStreamingAsync<string>(function))
        {
            Assert.Equal(fakeService.GetStreamingChatMessageContentsResult![updateIndex].Content, update);
            updateIndex++;
        }

        Assert.Equal(updateIndex, fakeService.GetStreamingChatMessageContentsResult.Count);
    }

    [Fact]
    public async Task ItConvertsFromSKStreamingChatMessageContentToItselfAsync()
    {
        var innerContent = new { test = "a" };
        var fakeService = new FakeChatCompletionService()
        {
            GetStreamingChatMessageContentsResult = [
                new StreamingChatMessageContent(AuthorRole.Assistant, "Hi! How can ") { InnerContent = innerContent },
                new StreamingChatMessageContent(null, "I assist you today?") { InnerContent = innerContent }
            ]
        };

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<IChatCompletionService>((sp) => fakeService);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("""
            <message role="system">You are a helpful assistant.</message>
            <message role="user">How many 20 cents can I get from 1 dollar?</message>
            """);

        // Act + Assert
        var updateIndex = 0;
        await foreach (var update in kernel.InvokeStreamingAsync<StreamingChatMessageContent>(function))
        {
            Assert.Same(fakeService.GetStreamingChatMessageContentsResult![updateIndex], update);
            updateIndex++;
        }

        Assert.Equal(updateIndex, fakeService.GetStreamingChatMessageContentsResult.Count);
    }

    [Fact]
    public async Task ItConvertsFromSKStreamingChatMessageContentToInnerContentAsync()
    {
        var innerContent = new Random();
        var fakeService = new FakeChatCompletionService()
        {
            GetStreamingChatMessageContentsResult = [
                new StreamingChatMessageContent(AuthorRole.Assistant, "Hi! How can ") { InnerContent = innerContent },
                new StreamingChatMessageContent(null, "I assist you today?") { InnerContent = innerContent }
            ]
        };

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<IChatCompletionService>((sp) => fakeService);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("""
            <message role="system">You are a helpful assistant.</message>
            <message role="user">How many 20 cents can I get from 1 dollar?</message>
            """);

        // Act + Assert
        var updateIndex = 0;
        await foreach (var update in kernel.InvokeStreamingAsync<Random>(function))
        {
            Assert.Same(fakeService.GetStreamingChatMessageContentsResult![updateIndex].InnerContent, update);
            updateIndex++;
        }

        Assert.Equal(updateIndex, fakeService.GetStreamingChatMessageContentsResult.Count);
    }

    [Fact]
    public async Task ItConvertsFromSKStreamingChatMessageContentToBytesAsync()
    {
        var innerContent = new Random();
        var fakeService = new FakeChatCompletionService()
        {
            GetStreamingChatMessageContentsResult = [
                new StreamingChatMessageContent(AuthorRole.Assistant, "Hi! How can ") { InnerContent = innerContent },
                new StreamingChatMessageContent(null, "I assist you today?") { InnerContent = innerContent }
            ]
        };

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<IChatCompletionService>((sp) => fakeService);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("""
            <message role="system">You are a helpful assistant.</message>
            <message role="user">How many 20 cents can I get from 1 dollar?</message>
            """);

        // Act + Assert
        var updateIndex = 0;
        await foreach (var update in kernel.InvokeStreamingAsync<byte[]>(function))
        {
            Assert.Equal(fakeService.GetStreamingChatMessageContentsResult![updateIndex].Content,
                        fakeService.GetStreamingChatMessageContentsResult![updateIndex].Encoding.GetString(update));

            updateIndex++;
        }

        Assert.Equal(updateIndex, fakeService.GetStreamingChatMessageContentsResult.Count);
    }

    /// <summary>
    /// This scenario covers scenarios on attempting to get a ChatResponseUpdate from a ITextGenerationService.
    /// </summary>
    [Fact]
    public async Task ItThrowsConvertingFromNonChatSKStreamingContentToMEAIChatResponseUpdate()
    {
        var fakeService = new FakeTextGenerationService()
        {
            GetStreamingTextContentsResult = [new StreamingTextContent("Hi!")]
        };

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<ITextGenerationService>((sp) => fakeService);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("How many 20 cents can I get from 1 dollar?");

        // Act + Assert
        await Assert.ThrowsAsync<NotSupportedException>(
            () => kernel.InvokeStreamingAsync<MEAI.ChatResponseUpdate>(function).GetAsyncEnumerator().MoveNextAsync().AsTask());
    }

    [Fact]
    public async Task ItThrowsWhenConvertingFromMEAIChatMessageUpdateWithNoDataContentToBytesAsync()
    {
        using var fakeService = new FakeChatClient()
        {
            GetStreamingResponseResult = [
                new MEAI.ChatResponseUpdate(MEAI.ChatRole.Assistant, "Hi! How can ")
            ]
        };

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<MEAI.IChatClient>((sp) => fakeService);
        Kernel kernel = builder.Build();

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt("""
            <message role="system">You are a helpful assistant.</message>
            <message role="user">How many 20 cents can I get from 1 dollar?</message>
            """);

        // Act + Assert
        await Assert.ThrowsAsync<NotSupportedException>(
            () => kernel.InvokeStreamingAsync<byte[]>(function).GetAsyncEnumerator().MoveNextAsync().AsTask());
    }

    public enum KernelInvocationType
    {
        InvokePrompt,
        InvokePromptStreaming,
        InvokeFunction,
        InvokeFunctionStreaming
    }

    #region private

    private sealed class FakeChatAsTextService : ITextGenerationService, IChatCompletionService
    {
        public IReadOnlyDictionary<string, object?> Attributes => throw new NotImplementedException();
        public ChatHistory? ChatHistory { get; private set; }

        public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            this.ChatHistory = chatHistory;

            return Task.FromResult<IReadOnlyList<ChatMessageContent>>([new(AuthorRole.Assistant, "Something")]);
        }

#pragma warning disable IDE0036 // Order modifiers
#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
        public async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
#pragma warning restore CS1998 // Async method lacks 'await' operators and will run synchronously
#pragma warning restore IDE0036 // Order modifiers
        {
            this.ChatHistory = chatHistory;
            yield return new StreamingChatMessageContent(AuthorRole.Assistant, "Something");
        }

        public IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }

        public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }
    }

    private sealed class FakeChatCompletionService : IChatCompletionService
    {
        public IReadOnlyDictionary<string, object?> Attributes => throw new NotImplementedException();

        public IList<StreamingChatMessageContent>? GetStreamingChatMessageContentsResult { get; set; }

        public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }

#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
        public async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
            ChatHistory chatHistory,
            PromptExecutionSettings? executionSettings = null,
            Kernel? kernel = null,
            [EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            foreach (var item in this.GetStreamingChatMessageContentsResult ?? [new StreamingChatMessageContent(AuthorRole.Assistant, "Something")])
            {
                yield return item;
            }
        }
#pragma warning restore CS1998 // Async method lacks 'await' operators and will run synchronously
    }

    private sealed class FakeTextGenerationService : ITextGenerationService
    {
        public IReadOnlyDictionary<string, object?> Attributes => throw new NotImplementedException();

        public IList<StreamingTextContent>? GetStreamingTextContentsResult { get; set; }

#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
        public async IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(
            string prompt,
            PromptExecutionSettings? executionSettings = null,
            Kernel? kernel = null,
            [EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            foreach (var item in this.GetStreamingTextContentsResult ?? [new StreamingTextContent("Something")])
            {
                yield return item;
            }
        }
#pragma warning restore CS1998 // Async method lacks 'await' operators and will run synchronously

        public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(string prompt, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }
    }

    private sealed class FakeChatClient : MEAI.IChatClient
    {
        public List<MEAI.ChatMessage>? ChatMessages { get; private set; }
        public List<MEAI.ChatResponseUpdate>? GetStreamingResponseResult { get; set; }

        public void Dispose()
        {
        }

        public Task<MEAI.ChatResponse> GetResponseAsync(IEnumerable<MEAI.ChatMessage> messages, MEAI.ChatOptions? options = null, CancellationToken cancellationToken = default)
        {
            this.ChatMessages = messages.ToList();
            return Task.FromResult(new MEAI.ChatResponse(new MEAI.ChatMessage(MEAI.ChatRole.Assistant, "Something")));
        }

        public object? GetService(Type serviceType, object? serviceKey = null)
        {
            return new MEAI.ChatClientMetadata();
        }

#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
        public async IAsyncEnumerable<MEAI.ChatResponseUpdate> GetStreamingResponseAsync(
            IEnumerable<MEAI.ChatMessage> messages,
            MEAI.ChatOptions? options = null,
            [EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            this.ChatMessages = messages.ToList();
            foreach (var item in this.GetStreamingResponseResult ?? [new MEAI.ChatResponseUpdate(MEAI.ChatRole.Assistant, "Something")])
            {
                yield return item;
            }
        }
#pragma warning restore CS1998 // Async method lacks 'await' operators and will run synchronously
    }

    private Mock<ITextGenerationService> GetMockTextGenerationService(IReadOnlyList<TextContent>? textContents = null)
    {
        var mockTextGenerationService = new Mock<ITextGenerationService>();

        mockTextGenerationService
            .Setup(l => l.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings?>(), It.IsAny<Kernel?>(), It.IsAny<CancellationToken>()))
            .Returns(Task.FromResult<IReadOnlyList<TextContent>>(textContents ?? [new TextContent("Default result")]));

        return mockTextGenerationService;
    }

    private Mock<IChatCompletionService> GetMockChatCompletionService(IReadOnlyList<ChatMessageContent>? chatMessageContents = null)
    {
        var mockChatCompletionService = new Mock<IChatCompletionService>();

        mockChatCompletionService
            .Setup(l => l.GetChatMessageContentsAsync(It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings?>(), It.IsAny<Kernel?>(), It.IsAny<CancellationToken>()))
            .Returns(Task.FromResult<IReadOnlyList<ChatMessageContent>>(chatMessageContents ?? [new(AuthorRole.Assistant, "Default result")]));

        return mockChatCompletionService;
    }

    private sealed class CustomTestType
    {
        public string Name { get; set; } = "MyCustomType";
    }
    #endregion
}

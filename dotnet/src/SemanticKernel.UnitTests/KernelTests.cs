// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.TextGeneration;
using Moq;
using Xunit;
using MEAI = Microsoft.Extensions.AI;

#pragma warning disable CS0618 // Events are deprecated

namespace SemanticKernel.UnitTests;

public class KernelTests
{
    private const string InputParameterName = "input";

    [Fact]
    public void ItProvidesAccessToFunctionsViaFunctionCollection()
    {
        // Arrange
        Kernel kernel = new();
        kernel.Plugins.AddFromType<MyPlugin>("mySk");

        // Act & Assert - 3 functions, var name is not case sensitive
        Assert.NotNull(kernel.Plugins.GetFunction("mySk", "sayhello"));
        Assert.NotNull(kernel.Plugins.GetFunction("MYSK", "SayHello"));
        Assert.NotNull(kernel.Plugins.GetFunction("mySk", "ReadFunctionCollectionAsync"));
        Assert.NotNull(kernel.Plugins.GetFunction("MYSK", "ReadFunctionCollectionAsync"));
    }

    [Fact]
    public async Task InvokeAsyncDoesNotRunWhenCancelledAsync()
    {
        // Arrange
        var kernel = new Kernel();
        var functions = kernel.ImportPluginFromType<MyPlugin>();

        using CancellationTokenSource cts = new();
        cts.Cancel();

        // Act
        await Assert.ThrowsAnyAsync<OperationCanceledException>(() => kernel.InvokeAsync(functions["GetAnyValue"], cancellationToken: cts.Token));
    }

    [Fact]
    public async Task InvokeAsyncRunsWhenNotCancelledAsync()
    {
        // Arrange
        var kernel = new Kernel();
        kernel.ImportPluginFromType<MyPlugin>("mySk");

        using CancellationTokenSource cts = new();

        // Act
        var result = await kernel.InvokeAsync(kernel.Plugins.GetFunction("mySk", "GetAnyValue"), cancellationToken: cts.Token);

        // Assert
        Assert.False(string.IsNullOrEmpty(result.GetValue<string>()));
    }

    [Fact]
    public void ItImportsPluginsNotCaseSensitive()
    {
        // Act
        KernelPlugin plugin = new Kernel().ImportPluginFromType<MyPlugin>();

        // Assert
        Assert.Equal(3, plugin.Count());
        Assert.True(plugin.Contains("GetAnyValue"));
        Assert.True(plugin.Contains("getanyvalue"));
        Assert.True(plugin.Contains("GETANYVALUE"));
    }

    [Fact]
    public void ItAllowsToImportTheSamePluginMultipleTimes()
    {
        // Arrange
        var kernel = new Kernel();

        // Act - Assert no exception occurs
        kernel.ImportPluginFromType<MyPlugin>();
        kernel.ImportPluginFromType<MyPlugin>("plugin1");
        kernel.ImportPluginFromType<MyPlugin>("plugin2");
        kernel.ImportPluginFromType<MyPlugin>("plugin3");
    }

    [Fact]
    public async Task ItReturnsFunctionResultsCorrectlyAsync()
    {
        // Arrange
        var kernel = new Kernel();

        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "Function1");

        // Act
        var result = await kernel.InvokeAsync(function);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("Result", result.GetValue<string>());
    }

    [Fact]
    public async Task ItCanFindAndRunFunctionAsync()
    {
        //Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "fake result", "function");

        var kernel = new Kernel();
        kernel.ImportPluginFromFunctions("plugin", [function]);

        //Act
        var result = await kernel.InvokeAsync("plugin", "function");

        //Assert
        Assert.NotNull(result);
        Assert.Equal("fake result", result.GetValue<string>());
    }

    [Fact]
    public void ItShouldBePossibleToSetAndGetCultureAssociatedWithKernel()
    {
        //Arrange
        var kernel = new Kernel();

        var culture = CultureInfo.GetCultureInfo(28);

        //Act
        kernel.Culture = culture;

        //Assert
        Assert.Equal(culture, kernel.Culture);
    }

    [Fact]
    public void ItDefaultsLoggerFactoryToNullLoggerFactory()
    {
        //Arrange
        var kernel = new Kernel();

        //Assert
        Assert.Same(NullLoggerFactory.Instance, kernel.LoggerFactory);
    }

    [Fact]
    public void ItDefaultsDataToEmptyDictionary()
    {
        //Arrange
        var kernel = new Kernel();

        //Assert
        Assert.Empty(kernel.Data);
    }

    [Fact]
    public void ItDefaultsPluginsToEmptyCollection()
    {
        //Arrange
        var kernel = new Kernel();

        //Assert
        Assert.Empty(kernel.Plugins);
    }

    [Fact]
    public void InvariantCultureShouldBeReturnedIfNoCultureWasAssociatedWithKernel()
    {
        //Arrange
        var kernel = new Kernel();

        //Act
        var culture = kernel.Culture;

        //Assert
        Assert.Same(CultureInfo.InvariantCulture, culture);
    }

    [Fact]
    public void ItDeepClonesAllRelevantStateInClone()
    {
        // Kernel with all properties set
        var serviceSelector = new Mock<IAIServiceSelector>();
        var loggerFactory = new Mock<ILoggerFactory>();
        var serviceProvider = new ServiceCollection()
            .AddSingleton(serviceSelector.Object)
#pragma warning disable CA2000 // Dispose objects before losing scope
            .AddSingleton(new HttpClient())
#pragma warning restore CA2000
            .AddSingleton(loggerFactory.Object)
            .AddSingleton<IFunctionInvocationFilter>(new MyFunctionFilter())
            .AddSingleton<IPromptRenderFilter>(new MyPromptFilter())
            .BuildServiceProvider();
        var plugin = KernelPluginFactory.CreateFromFunctions("plugin1");
        var plugins = new KernelPluginCollection() { plugin };
        Kernel kernel1 = new(serviceProvider, plugins);
        kernel1.Data["key"] = "value";

        // Clone and validate it
        Kernel kernel2 = kernel1.Clone();
        Assert.Same(kernel1.Services, kernel2.Services);
        Assert.Same(kernel1.Culture, kernel2.Culture);
        Assert.NotSame(kernel1.Data, kernel2.Data);
        Assert.Equal(kernel1.Data.Count, kernel2.Data.Count);
        Assert.Equal(kernel1.Data["key"], kernel2.Data["key"]);
        Assert.NotSame(kernel1.Plugins, kernel2.Plugins);
        Assert.Equal(kernel1.Plugins, kernel2.Plugins);
        this.AssertFilters(kernel1, kernel2);

        // Minimally configured kernel
        Kernel kernel3 = new();

        // Clone and validate it
        Kernel kernel4 = kernel3.Clone();
        Assert.Same(kernel3.Services, kernel4.Services);
        Assert.NotSame(kernel3.Data, kernel4.Data);
        Assert.Empty(kernel4.Data);
        Assert.NotSame(kernel1.Plugins, kernel2.Plugins);
        Assert.Empty(kernel4.Plugins);
        this.AssertFilters(kernel3, kernel4);
    }

    [Fact]
    public async Task InvokeStreamingAsyncCallsConnectorStreamingApiAsync()
    {
        // Arrange
        var mockTextCompletion = this.SetupStreamingMocks(
            new StreamingTextContent("chunk1"),
            new StreamingTextContent("chunk2"));
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<ITextGenerationService>(mockTextCompletion.Object);
        Kernel kernel = builder.Build();
        var prompt = "Write a simple phrase about UnitTests {{$input}}";
        var sut = KernelFunctionFactory.CreateFromPrompt(prompt);
        var variables = new KernelArguments() { [InputParameterName] = "importance" };

        var chunkCount = 0;
        // Act
        await foreach (var chunk in sut.InvokeStreamingAsync<StreamingKernelContent>(kernel, variables))
        {
            chunkCount++;
        }

        // Assert
        Assert.Equal(2, chunkCount);
        mockTextCompletion.Verify(m => m.GetStreamingTextContentsAsync(It.IsIn("Write a simple phrase about UnitTests importance"), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Exactly(1));
    }

    [Fact]
    public async Task InvokeStreamingAsyncCallsWithMEAIContentsAndChatCompletionApiAsync()
    {
        // Arrange
        var mockChatCompletion = this.SetupStreamingChatCompletionMocks(
            new StreamingChatMessageContent(AuthorRole.User, "chunk1"),
            new StreamingChatMessageContent(AuthorRole.User, "chunk2"));

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<IChatCompletionService>(mockChatCompletion.Object);
        Kernel kernel = builder.Build();
        var prompt = "Write a simple phrase about UnitTests {{$input}}";
        var expectedPrompt = prompt.Replace("{{$input}}", "importance");
        var sut = KernelFunctionFactory.CreateFromPrompt(prompt);
        var variables = new KernelArguments() { [InputParameterName] = "importance" };

        var chunkCount = 0;

        // Act & Assert
        await foreach (var chunk in sut.InvokeStreamingAsync<MEAI.ChatResponseUpdate>(kernel, variables))
        {
            Assert.Contains("chunk", chunk.Text);
            chunkCount++;
        }

        Assert.Equal(2, chunkCount);
        mockChatCompletion.Verify(m => m.GetStreamingChatMessageContentsAsync(It.Is<ChatHistory>((m) => m[0].Content == expectedPrompt), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>()), Times.Exactly(1));
    }

    [Fact]
    public async Task InvokeStreamingAsyncGenericPermutationsCallsConnectorChatClientAsync()
    {
        // Arrange
        var customRawItem = new MEAI.ChatOptions();
        var mockChatClient = this.SetupStreamingChatClientMock(
            new MEAI.ChatResponseUpdate(role: MEAI.ChatRole.Assistant, content: "chunk1") { RawRepresentation = customRawItem },
            new MEAI.ChatResponseUpdate(role: null, content: "chunk2") { RawRepresentation = customRawItem });
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<MEAI.IChatClient>(mockChatClient.Object);
        Kernel kernel = builder.Build();
        var prompt = "Write a simple phrase about UnitTests {{$input}}";
        var expectedPrompt = prompt.Replace("{{$input}}", "importance");
        var sut = KernelFunctionFactory.CreateFromPrompt(prompt);
        var variables = new KernelArguments() { [InputParameterName] = "importance" };

        var totalChunksExpected = 0;
        var totalInvocationTimesExpected = 0;

        // Act & Assert
        totalInvocationTimesExpected++;
        await foreach (var chunk in sut.InvokeStreamingAsync<string>(kernel, variables))
        {
            Assert.Contains("chunk", chunk);
            totalChunksExpected++;
        }

        totalInvocationTimesExpected++;
        await foreach (var chunk in sut.InvokeStreamingAsync<StreamingKernelContent>(kernel, variables))
        {
            totalChunksExpected++;
            Assert.Same(customRawItem, chunk.InnerContent);
        }

        totalInvocationTimesExpected++;
        await foreach (var chunk in sut.InvokeStreamingAsync<StreamingChatMessageContent>(kernel, variables))
        {
            Assert.Contains("chunk", chunk.Content);
            Assert.Same(customRawItem, chunk.InnerContent);
            totalChunksExpected++;
        }

        totalInvocationTimesExpected++;
        await foreach (var chunk in sut.InvokeStreamingAsync<MEAI.ChatResponseUpdate>(kernel, variables))
        {
            Assert.Contains("chunk", chunk.Text);
            Assert.Same(customRawItem, chunk.RawRepresentation);
            totalChunksExpected++;
        }

        totalInvocationTimesExpected++;
        await foreach (var chunk in sut.InvokeStreamingAsync<MEAI.AIContent>(kernel, variables))
        {
            Assert.Contains("chunk", chunk.ToString());
            totalChunksExpected++;
        }

        totalInvocationTimesExpected++;
        await foreach (var chunk in sut.InvokeStreamingAsync<IList<MEAI.AIContent>>(kernel, variables))
        {
            Assert.Contains("chunk", chunk[0].ToString());
            totalChunksExpected++;
        }

        totalInvocationTimesExpected++;
        await foreach (var chunk in sut.InvokeStreamingAsync<MEAI.TextContent>(kernel, variables))
        {
            Assert.Contains("chunk", chunk.Text);
            totalChunksExpected++;
        }

        Assert.Equal(totalInvocationTimesExpected * 2, totalChunksExpected);
        mockChatClient.Verify(m => m.GetStreamingResponseAsync(It.Is<IList<MEAI.ChatMessage>>((m) => m[0].Text == expectedPrompt), It.IsAny<MEAI.ChatOptions>(), It.IsAny<CancellationToken>()), Times.Exactly(totalInvocationTimesExpected));
    }

    [Fact]
    public async Task ValidateInvokeAsync()
    {
        // Arrange
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => "ExpectedResult");

        // Act
        var result = await kernel.InvokeAsync(function);

        // Assert
        Assert.NotNull(result.Value);
        Assert.Equal("ExpectedResult", result.Value);
    }

    [Fact]
    public async Task ValidateInvokePromptAsync()
    {
        // Arrange
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<IChatCompletionService>((sp) => new FakeChatCompletionService("ExpectedResult"));
        Kernel kernel = builder.Build();

        // Act
        var result = await kernel.InvokePromptAsync("My Test Prompt");

        // Assert
        Assert.NotNull(result.Value);
        Assert.Equal("ExpectedResult", result.Value.ToString());
    }

    private sealed class FakeChatCompletionService(string result) : IChatCompletionService
    {
        public IReadOnlyDictionary<string, object?> Attributes { get; } = new Dictionary<string, object?>();

        public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            return Task.FromResult<IReadOnlyList<ChatMessageContent>>([new(AuthorRole.Assistant, result)]);
        }

#pragma warning disable IDE0036 // Order modifiers
#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
        public async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
#pragma warning restore CS1998 // Async method lacks 'await' operators and will run synchronously
#pragma warning restore IDE0036 // Order modifiers
        {
            yield return new StreamingChatMessageContent(AuthorRole.Assistant, result);
        }
    }

    private (TextContent mockTextContent, Mock<ITextGenerationService> textCompletionMock) SetupMocks(string? completionResult = null)
    {
        var mockTextContent = new TextContent(completionResult ?? "LLM Result about UnitTests");

        var mockTextCompletion = new Mock<ITextGenerationService>();
        mockTextCompletion.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync([mockTextContent]);
        return (mockTextContent, mockTextCompletion);
    }

    private Mock<IChatCompletionService> SetupStreamingChatCompletionMocks(params StreamingChatMessageContent[] streamingContents)
    {
        var mockChatCompletion = new Mock<IChatCompletionService>();
        mockChatCompletion.Setup(m => m.GetStreamingChatMessageContentsAsync(It.IsAny<ChatHistory>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).Returns(streamingContents.ToAsyncEnumerable());
        return mockChatCompletion;
    }

    private Mock<ITextGenerationService> SetupStreamingMocks(params StreamingTextContent[] streamingContents)
    {
        var mockTextCompletion = new Mock<ITextGenerationService>();
        mockTextCompletion.Setup(m => m.GetStreamingTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).Returns(streamingContents.ToAsyncEnumerable());

        return mockTextCompletion;
    }

    private Mock<MEAI.IChatClient> SetupStreamingChatClientMock(params MEAI.ChatResponseUpdate[] chatResponseUpdates)
    {
        var mockChatClient = new Mock<MEAI.IChatClient>();
        mockChatClient.Setup(m => m.GetStreamingResponseAsync(It.IsAny<IList<MEAI.ChatMessage>>(), It.IsAny<MEAI.ChatOptions>(), It.IsAny<CancellationToken>())).Returns(chatResponseUpdates.ToAsyncEnumerable());
        mockChatClient.Setup(c => c.GetService(typeof(MEAI.ChatClientMetadata), It.IsAny<object?>())).Returns(new MEAI.ChatClientMetadata());

        return mockChatClient;
    }

    private void AssertFilters(Kernel kernel1, Kernel kernel2)
    {
        var functionFilters1 = kernel1.GetAllServices<IFunctionInvocationFilter>().ToArray();
        var promptFilters1 = kernel1.GetAllServices<IPromptRenderFilter>().ToArray();

        var functionFilters2 = kernel2.GetAllServices<IFunctionInvocationFilter>().ToArray();
        var promptFilters2 = kernel2.GetAllServices<IPromptRenderFilter>().ToArray();

        Assert.Equal(functionFilters1.Length, functionFilters2.Length);

        for (var i = 0; i < functionFilters1.Length; i++)
        {
            Assert.Same(functionFilters1[i], functionFilters2[i]);
        }

        Assert.Equal(promptFilters1.Length, promptFilters2.Length);

        for (var i = 0; i < promptFilters1.Length; i++)
        {
            Assert.Same(promptFilters1[i], promptFilters2[i]);
        }
    }

    public class MyPlugin
    {
        [KernelFunction, Description("Return any value.")]
        public virtual string GetAnyValue()
        {
            return Guid.NewGuid().ToString();
        }

        [KernelFunction, Description("Just say hello")]
        public virtual void SayHello()
        {
            Console.WriteLine("Hello folks!");
        }

        [KernelFunction("ReadFunctionCollectionAsync"), Description("Export info.")]
        public async Task ReadFunctionCollectionAsync(Kernel kernel)
        {
            await Task.Delay(0);
            Assert.NotNull(kernel.Plugins);
        }
    }

    private sealed class MyFunctionFilter : IFunctionInvocationFilter
    {
        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            await next(context);
        }
    }

    private sealed class MyPromptFilter : IPromptRenderFilter
    {
        public async Task OnPromptRenderAsync(PromptRenderContext context, Func<PromptRenderContext, Task> next)
        {
            await next(context);
        }
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.ChatCompletion.TextWrapper;
using Microsoft.SemanticKernel.AI.TextCompletion;
using SemanticKernel.IntegrationTests.Planning.StepwisePlanner;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Abstractions;
public sealed class TextWrapperTests : IDisposable
{
    private const string systemMessage = "You are a helpful AI assistant";

    public TextWrapperTests(ITestOutputHelper output)
    {
        this._loggerFactory = NullLoggerFactory.Instance;
        this._testOutputHelper = new RedirectOutput(output);

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<StepwisePlannerTests>()
            .Build();
    }

    [Theory]
    [InlineData("What are the first five digits of pi", "3.1415", true)]
    [InlineData("What are the first five digits of pi", "3.1415", false)]
    public async Task CanGetCompletion(string prompt, string partialExpectedAnswer, bool useWrappedCompletion)
    {
        // Arrange
        IChatCompletion chatCompletion = this.GetChatCompletion(useWrappedCompletion);
        ChatHistory chat = chatCompletion.CreateNewChat(systemMessage);
        chat.AddUserMessage(prompt);

        // Act
        IReadOnlyList<IChatResult> results = await chatCompletion.GetChatCompletionsAsync(chat);

        // Assert
        IChatResult chatResult = results.Single();
        ChatMessageBase message = await chatResult.GetChatMessageAsync();
        Assert.Equal(AuthorRole.Assistant, message.Role);
        Assert.Contains(partialExpectedAnswer, message.Content, StringComparison.InvariantCultureIgnoreCase);
    }

    [Theory]
    [InlineData("What are the first five digits of pi", "3.1415", true)]
    [InlineData("What are the first five digits of pi", "3.1415", false)]
    public async Task CanGetStreamingCompletion(string prompt, string partialExpectedAnswer, bool useWrappedCompletion)
    {
        // Arrange
        IChatCompletion chatCompletion = this.GetChatCompletion(useWrappedCompletion);
        ChatHistory chat = chatCompletion.CreateNewChat(systemMessage);
        chat.AddUserMessage(prompt);
        var chatRequestSettings = new ChatRequestSettings
        {
            MaxTokens = 50
        };

        // Act
        IAsyncEnumerable<IChatStreamingResult> results = chatCompletion.GetStreamingChatCompletionsAsync(chat, chatRequestSettings);

        // Assert
        var sb = new StringBuilder();
        int numResults = 0;
        await foreach (IChatStreamingResult result in results)
        {
            await foreach (ChatMessageBase message in result.GetStreamingChatMessageAsync())
            {
                Assert.Equal(AuthorRole.Assistant, message.Role);
                sb.Append(message.Content);
                numResults++;
            }
        }

        Assert.Contains(partialExpectedAnswer, sb.ToString(), StringComparison.InvariantCultureIgnoreCase);
        Assert.True(numResults > 1, numResults.ToString());
    }

    private IChatCompletion GetChatCompletion(bool useWrappedChatModel)
    {
        var kernel = this.InitializeKernel(!useWrappedChatModel);

        if (useWrappedChatModel)
        {
            var textCompletion = kernel.GetService<ITextCompletion>();
            return new TextCompletionChatWrapper(textCompletion);
        }

        return kernel.GetService<IChatCompletion>();
    }

    private IKernel InitializeKernel(bool useChatModel)
    {
        return TestHelpers.InitializeAzureOpenAiKernelBuilder(
                this._configuration,
                this._loggerFactory,
                false,
                useChatModel)
            .Build();
    }

    private readonly ILoggerFactory _loggerFactory;
    private readonly RedirectOutput _testOutputHelper;
    private readonly IConfigurationRoot _configuration;

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    ~TextWrapperTests()
    {
        this.Dispose(false);
    }

    private void Dispose(bool disposing)
    {
        if (disposing)
        {
            if (this._loggerFactory is IDisposable ld)
            {
                ld.Dispose();
            }

            this._testOutputHelper.Dispose();
        }
    }
}

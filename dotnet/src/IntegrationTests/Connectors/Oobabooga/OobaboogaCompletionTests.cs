// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Net.WebSockets;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.TextCompletion;
using Xunit;
using ChatHistory = Microsoft.SemanticKernel.AI.ChatCompletion.ChatHistory;

namespace SemanticKernel.IntegrationTests.Connectors.Oobabooga;

/// <summary>
/// Integration tests for <see cref=" Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.ChatCompletion.OobaboogaChatCompletion"/>.
/// </summary>
public sealed class OobaboogaCompletionTests : IDisposable
{
    private const string Endpoint = "http://localhost";
    private const int BlockingPort = 5000;
    private const int StreamingPort = 5005;

    private readonly IConfigurationRoot _configuration;
    private List<ClientWebSocket> _webSockets = new();
    private Func<ClientWebSocket> _webSocketFactory;

    public OobaboogaCompletionTests()
    {
        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .Build();
        this._webSocketFactory = () =>
        {
            var toReturn = new ClientWebSocket();
            this._webSockets.Add(toReturn);
            return toReturn;
        };
    }

    private const string Input = " My name is";

    [Fact(Skip = "This test is for manual verification.")]
    public async Task OobaboogaLocalTextCompletionAsync()
    {
        var oobaboogaLocal = new OobaboogaTextCompletion(
            endpoint: new Uri(Endpoint),
            blockingPort: BlockingPort);

        // Act
        var localResponse = await oobaboogaLocal.CompleteAsync(Input, new CompleteRequestSettings()
        {
            Temperature = 0.01,
            MaxTokens = 7,
            TopP = 0.1,
        });

        AssertAcceptableResponse(localResponse);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task OobaboogaLocalTextCompletionStreamingAsync()
    {
        var oobaboogaLocal = new OobaboogaTextCompletion(
            endpoint: new Uri(Endpoint),
            streamingPort: StreamingPort,
            webSocketFactory: this._webSocketFactory);

        // Act
        var localResponse = oobaboogaLocal.CompleteStreamAsync(Input, new CompleteRequestSettings()
        {
            Temperature = 0.01,
            MaxTokens = 7,
            TopP = 0.1,
        });

        StringBuilder stringBuilder = new();
        await foreach (var result in localResponse)
        {
            stringBuilder.Append(result);
        }

        var resultsMerged = stringBuilder.ToString();
        AssertAcceptableResponse(resultsMerged);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task OobaboogaLocalChatCompletionAsync()
    {
        var oobaboogaLocal = new OobaboogaChatCompletion(
            endpoint: new Uri(Endpoint),
            blockingPort: BlockingPort);

        var history = new ChatHistory();
        history.AddUserMessage("What is your name?");
        // Act
        var localResponse = await oobaboogaLocal.GetChatCompletionsAsync(history, new ChatRequestSettings()
        {
            Temperature = 0.01,
            MaxTokens = 20,
            TopP = 0.1,
        });

        var chatMessage = await localResponse[^1].GetChatMessageAsync(CancellationToken.None).ConfigureAwait(false);
        this.AssertAcceptableChatResponse(chatMessage);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task OobaboogaLocalChatCompletionStreamingAsync()
    {
        var oobaboogaLocal = new OobaboogaChatCompletion(
            endpoint: new Uri(Endpoint),
            blockingPort: BlockingPort,
            streamingPort: StreamingPort);

        var history = new ChatHistory();
        history.AddUserMessage("What is your name?");

        // Act
        var localResponse = oobaboogaLocal.GetStreamingChatCompletionsAsync(history, new ChatRequestSettings()
        {
            Temperature = 0.01,
            MaxTokens = 7,
            TopP = 0.1,
        });

        StringBuilder stringBuilder = new();
        ChatMessageBase? chatMessage = null;
        await foreach (var result in localResponse)
        {
            await foreach (var message in result.GetStreamingChatMessageAsync())
            {
                stringBuilder.AppendLine(CultureInfo.InvariantCulture, $"{message.Role}: {message.Content}");
                chatMessage = message;
            }
        }

        var resultsMerged = stringBuilder.ToString();
        this.AssertAcceptableChatResponse(chatMessage);
    }

    private static void AssertAcceptableResponse(string localResponse)
    {
        // Assert
        Assert.NotNull(localResponse);
        // Depends on the target LLM obviously, but most LLMs should propose an arbitrary surname preceded by a white space, including the start prompt or not
        // ie "  My name is" => " John (...)" or "  My name is" => " My name is John (...)".
        // Here are a couple LLMs that were tested successfully: gpt2, aisquared_dlite-v1-355m, bigscience_bloomz-560m,  eachadea_vicuna-7b-1.1, TheBloke_WizardLM-30B-GPTQ etc.
        // A few will return an empty string, but well those shouldn't be used for integration tests.
        var expectedRegex = new Regex(@"\s\w+.*");
        Assert.Matches(expectedRegex, localResponse);
    }

    private void AssertAcceptableChatResponse(ChatMessageBase? chatMessage)
    {
        Assert.NotNull(chatMessage);
        Assert.NotNull(chatMessage.Content);
        Assert.Equal(chatMessage.Role, AuthorRole.Assistant);
        // Default chat settings use the "Example" character, which depicts an assistant named Chiharu. Any non trivial chat model should return the appropriate name.
        var expectedRegex = new Regex(@"\w+.*Chiharu.*");
        Assert.Matches(expectedRegex, chatMessage.Content);
    }

    public void Dispose()
    {
        foreach (ClientWebSocket clientWebSocket in this._webSockets)
        {
            clientWebSocket.Dispose();
        }
    }
}

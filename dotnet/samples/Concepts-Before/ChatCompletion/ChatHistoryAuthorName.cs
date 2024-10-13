// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace ChatCompletion;

// The following example shows how to use Chat History with Author identity associated with each chat message.
public class ChatHistoryAuthorName(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Flag to force usage of OpenAI configuration if both <see cref="TestConfiguration.OpenAI"/>
    /// and <see cref="TestConfiguration.AzureOpenAI"/> are defined.
    /// If 'false', Azure takes precedence.
    /// </summary>
    /// <remarks>
    /// NOTE: Retrieval tools is not currently available on Azure.
    /// </remarks>
    private new const bool ForceOpenAI = true;

    private static readonly OpenAIPromptExecutionSettings s_executionSettings =
        new()
        {
            FrequencyPenalty = 0,
            PresencePenalty = 0,
            Temperature = 1,
            TopP = 0.5,
        };

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task CompletionIdentityAsync(bool withName)
    {
        Console.WriteLine("======== Completion Identity ========");

        IChatCompletionService chatService = CreateCompletionService();

        ChatHistory chatHistory = CreateHistory(withName);

        WriteMessages(chatHistory);

        WriteMessages(await chatService.GetChatMessageContentsAsync(chatHistory, s_executionSettings), chatHistory);

        ValidateMessages(chatHistory, withName);
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task StreamingIdentityAsync(bool withName)
    {
        Console.WriteLine("======== Completion Identity ========");

        IChatCompletionService chatService = CreateCompletionService();

        ChatHistory chatHistory = CreateHistory(withName);

        var content = await chatHistory.AddStreamingMessageAsync(chatService.GetStreamingChatMessageContentsAsync(chatHistory, s_executionSettings).Cast<OpenAIStreamingChatMessageContent>()).ToArrayAsync();

        WriteMessages(chatHistory);

        ValidateMessages(chatHistory, withName);
    }

    private static ChatHistory CreateHistory(bool withName)
    {
        return
            [
                new ChatMessageContent(AuthorRole.System, "Write one paragraph in response to the user that rhymes") { AuthorName = withName ? "Echo" : null },
                new ChatMessageContent(AuthorRole.User, "Why is AI awesome") { AuthorName = withName ? "Ralph" : null },
            ];
    }

    private void ValidateMessages(ChatHistory chatHistory, bool expectName)
    {
        foreach (var message in chatHistory)
        {
            if (expectName && message.Role != AuthorRole.Assistant)
            {
                Assert.NotNull(message.AuthorName);
            }
            else
            {
                Assert.Null(message.AuthorName);
            }
        }
    }

    private void WriteMessages(IReadOnlyList<ChatMessageContent> messages, ChatHistory? history = null)
    {
        foreach (var message in messages)
        {
            Console.WriteLine($"# {message.Role}:{message.AuthorName ?? "?"} - {message.Content ?? "-"}");
        }

        history?.AddRange(messages);
    }

    private static IChatCompletionService CreateCompletionService()
    {
        return
            ForceOpenAI || string.IsNullOrEmpty(TestConfiguration.AzureOpenAI.Endpoint) ?
                new OpenAIChatCompletionService(
                    TestConfiguration.OpenAI.ChatModelId,
                    TestConfiguration.OpenAI.ApiKey) :
                new AzureOpenAIChatCompletionService(
                    deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                    endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                    apiKey: TestConfiguration.AzureOpenAI.ApiKey,
                    modelId: TestConfiguration.AzureOpenAI.ChatModelId);
    }
}

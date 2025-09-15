// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.MistralAI;

namespace ChatCompletion;

// The following example shows how to use Semantic Kernel with MistralAI API
public class MistralAI_ChatCompletion(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task GetChatMessageContentAsync()
    {
        Assert.NotNull(TestConfiguration.MistralAI.ChatModelId);
        Assert.NotNull(TestConfiguration.MistralAI.ApiKey);

        MistralAIChatCompletionService chatService = new(
            modelId: TestConfiguration.MistralAI.ChatModelId,
            apiKey: TestConfiguration.MistralAI.ApiKey);

        var chatHistory = new ChatHistory("You are a librarian, expert about books");

        chatHistory.AddUserMessage("Hi, I'm looking for book suggestions");
        this.OutputLastMessage(chatHistory);

        var reply = await chatService.GetChatMessageContentAsync(chatHistory, new MistralAIPromptExecutionSettings { MaxTokens = 200 });
        Console.WriteLine(reply);
    }

    [Fact]
    public async Task GetChatMessageContentUsingImageContentAsync()
    {
        Assert.NotNull(TestConfiguration.MistralAI.ImageModelId);
        Assert.NotNull(TestConfiguration.MistralAI.ApiKey);

        // Create a logging handler to output HTTP requests and responses
        var handler = new LoggingHandler(new HttpClientHandler(), this.Output);
        var httpClient = new HttpClient(handler);

        MistralAIChatCompletionService chatService = new(
            modelId: TestConfiguration.MistralAI.ImageModelId,
            apiKey: TestConfiguration.MistralAI.ApiKey,
            httpClient: httpClient);

        var chatHistory = new ChatHistory();

        var chatMessage = new ChatMessageContent(AuthorRole.User, "What's in this image?");
        chatMessage.Items.Add(new ImageContent("data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEA2ADYAAD/2wBDAAIBAQIBAQICAgICAgICAwUDAwMDAwYEBAMFBwYHBwcGBwcICQsJCAgKCAcHCg0KCgsMDAwMBwkODw0MDgsMDAz/2wBDAQICAgMDAwYDAwYMCAcIDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAz/wAARCAAQABADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD5rooor8DP9oD/2Q=="));

        chatHistory.Add(chatMessage);
        this.OutputLastMessage(chatHistory);

        var reply = await chatService.GetChatMessageContentAsync(chatHistory, new MistralAIPromptExecutionSettings { MaxTokens = 200 });
        Console.WriteLine(reply);
    }
}

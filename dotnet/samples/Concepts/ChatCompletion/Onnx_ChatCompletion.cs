// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Onnx;

namespace ChatCompletion;

// The following example shows how to use Semantic Kernel with Onnx Gen AI Chat Completion API
public class Onnx_ChatCompletion(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Example using the service directly to get chat message content
    /// </summary>
    /// <remarks>
    /// Configuration example:
    /// <list type="table">
    /// <item>
    /// <term>ModelId:</term>
    /// <description>phi-3</description>
    /// </item>
    /// <item>
    /// <term>ModelPath:</term>
    /// <description>D:\huggingface\Phi-3-mini-4k-instruct-onnx\cpu_and_mobile\cpu-int4-rtn-block-32</description>
    /// </item>
    /// </list>
    /// </remarks>
    [Fact]
    public async Task ServicePromptAsync()
    {
        Assert.NotNull(TestConfiguration.Onnx.ModelId);   // dotnet user-secrets set "Onnx:ModelId" "<model-id>"
        Assert.NotNull(TestConfiguration.Onnx.ModelPath); // dotnet user-secrets set "Onnx:ModelPath" "<model-folder-path>"

        Console.WriteLine("======== Onnx - Chat Completion ========");

        using var chatService = new OnnxRuntimeGenAIChatCompletionService(
            modelId: TestConfiguration.Onnx.ModelId,
            modelPath: TestConfiguration.Onnx.ModelPath);

        Console.WriteLine("Chat content:");
        Console.WriteLine("------------------------");

        var chatHistory = new ChatHistory("You are a librarian, expert about books");

        // First user message
        chatHistory.AddUserMessage("Hi, I'm looking for book suggestions");
        OutputLastMessage(chatHistory);

        // First assistant message
        var reply = await chatService.GetChatMessageContentAsync(chatHistory);
        chatHistory.Add(reply);
        OutputLastMessage(chatHistory);

        // Second user message
        chatHistory.AddUserMessage("I love history and philosophy, I'd like to learn something new about Greece, any suggestion");
        OutputLastMessage(chatHistory);

        // Second assistant message
        reply = await chatService.GetChatMessageContentAsync(chatHistory);
        chatHistory.Add(reply);
        OutputLastMessage(chatHistory);
    }

    /// <summary>
    /// Example using the kernel to send a chat history and get a chat message content
    /// </summary>
    /// <remarks>
    /// Configuration example:
    /// <list type="table">
    /// <item>
    /// <term>ModelId:</term>
    /// <description>phi-3</description>
    /// </item>
    /// <item>
    /// <term>ModelPath:</term>
    /// <description>D:\huggingface\Phi-3-mini-4k-instruct-onnx\cpu_and_mobile\cpu-int4-rtn-block-32</description>
    /// </item>
    /// </list>
    /// </remarks>
    [Fact]
    public async Task ChatPromptAsync()
    {
        Assert.NotNull(TestConfiguration.Onnx.ModelId);   // dotnet user-secrets set "Onnx:ModelId" "<model-id>"
        Assert.NotNull(TestConfiguration.Onnx.ModelPath); // dotnet user-secrets set "Onnx:ModelPath" "<model-folder-path>"

        Console.WriteLine("======== Onnx - Chat Prompt Completion ========");

        StringBuilder chatPrompt = new("""
                                       <message role="system">You are a librarian, expert about books</message>
                                       <message role="user">Hi, I'm looking for book suggestions</message>
                                       """);

        var kernel = Kernel.CreateBuilder()
            .AddOnnxRuntimeGenAIChatCompletion(
                serviceId: TestConfiguration.Onnx.ModelId,
                modelId: TestConfiguration.Onnx.ModelId,
                modelPath: TestConfiguration.Onnx.ModelPath)
            .Build();

        var reply = await kernel.InvokePromptAsync(chatPrompt.ToString());

        chatPrompt.AppendLine($"<message role=\"assistant\"><![CDATA[{reply}]]></message>");
        chatPrompt.AppendLine("<message role=\"user\">I love history and philosophy, I'd like to learn something new about Greece, any suggestion</message>");

        reply = await kernel.InvokePromptAsync(chatPrompt.ToString());

        Console.WriteLine(reply);

        DisposeServices(kernel);
    }

    /// <summary>
    /// To avoid any potential memory leak all disposable services created by the kernel are disposed.
    /// </summary>
    /// <param name="kernel">Target kernel</param>
    private static void DisposeServices(Kernel kernel)
    {
        foreach (var target in kernel
            .GetAllServices<IChatCompletionService>()
            .OfType<IDisposable>())
        {
            target.Dispose();
        }
    }
}

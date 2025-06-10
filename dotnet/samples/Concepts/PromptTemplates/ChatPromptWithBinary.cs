// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Resources;

namespace PromptTemplates;

/// <summary>
/// This example demonstrates how to use ChatPrompt XML format with Binary content types.
/// The new ChatPrompt parser supports &lt;binary&gt; tags for various document formats like PDF, Word, CSV, etc.
/// </summary>
public class ChatPromptWithBinary(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Demonstrates using binary content (PDF file) in ChatPrompt XML format with data URI.
    /// </summary>
    [Fact]
    public async Task ChatPromptWithBinaryContentDataUri()
    {
        // Load a PDF file and convert to base64 data URI
        var fileBytes = await EmbeddedResource.ReadAllAsync("employees.pdf");
        var fileBase64 = Convert.ToBase64String(fileBytes.ToArray());
        var dataUri = $"data:application/pdf;base64,{fileBase64}";

        var chatPrompt = $"""
            <message role="system">You are a helpful assistant that can analyze documents.</message>
            <message role="user">
                <text>Please analyze this PDF document and provide a summary of its contents.</text>
                <binary>{dataUri}</binary>
            </message>
            """;

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        var chatFunction = kernel.CreateFunctionFromPrompt(chatPrompt);
        var result = await kernel.InvokeAsync(chatFunction);

        Console.WriteLine("=== ChatPrompt with Binary Content (Data URI) ===");
        Console.WriteLine("Prompt:");
        Console.WriteLine(chatPrompt);
        Console.WriteLine("\nResult:");
        Console.WriteLine(result);
    }

    /// <summary>
    /// Demonstrates a conversation flow using ChatPrompt with binary content across multiple messages.
    /// </summary>
    [Fact]
    public async Task ChatPromptConversationWithBinaryContent()
    {
        var pdfBytes = await EmbeddedResource.ReadAllAsync("employees.pdf");
        var pdfBase64 = Convert.ToBase64String(pdfBytes.ToArray());
        var pdfDataUri = $"data:application/pdf;base64,{pdfBase64}";

        var chatPrompt = $"""
            <message role="system">You are a helpful assistant that can analyze documents and provide insights.</message>
            <message role="user">
                <text>I have a document that I need help understanding. Can you analyze it?</text>
                <binary>{pdfDataUri}</binary>
            </message>
            <message role="assistant">I can see this is a PDF document about employees. Let me analyze its contents for you. The document appears to contain employee information and organizational data. What specific aspects would you like me to focus on?</message>
            <message role="user">
                <text>Can you extract the key information and create a summary? Also, what format would be best for sharing this information with my team?</text>
            </message>
            """;

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        var chatFunction = kernel.CreateFunctionFromPrompt(chatPrompt);
        var result = await kernel.InvokeAsync(chatFunction);

        Console.WriteLine("=== ChatPrompt Conversation with Binary Content ===");
        Console.WriteLine("Prompt (showing conversation flow):");
        Console.WriteLine(chatPrompt[..Math.Min(800, chatPrompt.Length)] + "...");
        Console.WriteLine("\nResult:");
        Console.WriteLine(result);
    }
}

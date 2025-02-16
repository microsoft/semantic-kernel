// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Chat;

#pragma warning disable SKEXP0110, SKEXP0001, SKEXP0050, CS8600, CS8604, SKEXP0010

namespace ReasoningEffortModels;

internal sealed class Program
{
    // Entry point: creates and runs three agents with different reasoning efforts.
    private static async Task Main(string[] args)
    {
        // Instantiate each agent with its designated reasoning effort
        var smartBlogPostAgent = new SmartBlogPostAgent(ChatReasoningEffortLevel.Low);
        var poemAgent = new PoemAgent(ChatReasoningEffortLevel.Medium);
        var codeExampleAgent = new CodeExampleAgent(ChatReasoningEffortLevel.High);

        // Demonstrate Smart Blog Post Agent (Low reasoning)
        Console.WriteLine("=== Smart Blog Post Demo (Low Reasoning) ===");
        var blogAgentInstance = smartBlogPostAgent.CreateAgent();
        await InvokeAgentAsync(blogAgentInstance, "Please generate a detailed blog post about Semantic Kernel that covers its architecture, benefits, and real-world applications.");

        // Demonstrate Poem Agent (Medium reasoning)
        Console.WriteLine("\n=== Poem Demo (Medium Reasoning) ===");
        var poemAgentInstance = poemAgent.CreateAgent();
        await InvokeAgentAsync(poemAgentInstance, "Write a creative, whimsical poem about Semantic Kernel and its innovative approach to artificial intelligence.");

        // Demonstrate Code Example Agent (High reasoning)
        Console.WriteLine("\n=== Code Example Demo (High Reasoning) ===");
        var codeAgentInstance = codeExampleAgent.CreateAgent();
        await InvokeAgentAsync(codeAgentInstance, "Show me a sample C# code snippet that demonstrates how to integrate Semantic Kernel into a creative project, including explanations for each step.");

        Console.WriteLine("Demo complete. Press any key to exit.");
        Console.ReadKey();
    }

    /// <summary>
    /// Helper method to invoke an agent with a given user prompt and print out the conversation.
    /// </summary>
    /// <param name="agent">The ChatCompletionAgent to invoke.</param>
    /// <param name="ask">The user prompt to send to the agent.</param>
    /// <returns>A Task representing the asynchronous operation.</returns>
    private static async Task InvokeAgentAsync(ChatCompletionAgent agent, string ask)
    {
        // Create a new chat history instance.
        ChatHistory chat = new();

        // Add the user message (the ask).
        Microsoft.SemanticKernel.ChatMessageContent userMessage = new(AuthorRole.User, ask);

        chat.Add(userMessage);
        Console.WriteLine($"> User: {ask}");

        // Invoke the agent asynchronously. The agent's InvokeAsync returns an async stream of responses.
        await foreach (var response in agent.InvokeAsync(chat))
        {
            // Add each agent response to the chat history and print it.
            chat.Add(response);
            Console.WriteLine($"> {response.Role}: {response.Content}");
        }
    }
}

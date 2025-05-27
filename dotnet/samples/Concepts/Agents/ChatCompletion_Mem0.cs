// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http.Headers;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Memory;

namespace Agents;

#pragma warning disable SKEXP0130 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

/// <summary>
/// Demonstrate creation of <see cref="ChatCompletionAgent"/> and
/// adding memory capabilities to it using https://mem0.ai/.
/// </summary>
public class ChatCompletion_Mem0(ITestOutputHelper output) : BaseTest(output)
{
    private const string AgentName = "FriendlyAssistant";
    private const string AgentInstructions = "You are a friendly assistant";

    /// <summary>
    /// Shows how to allow an agent to remember user preferences across multiple threads.
    /// </summary>
    [Fact]
    private async Task UseMemoryAsync()
    {
        // Create a new HttpClient with the base address of the mem0 service and a token for authentication.
        using var httpClient = new HttpClient()
        {
            BaseAddress = new Uri(TestConfiguration.Mem0.BaseAddress ?? "https://api.mem0.ai")
        };
        httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Token", TestConfiguration.Mem0.ApiKey);

        // Create a mem0 component with the current user's id, so that it stores memories for that user.
        var mem0Provider = new Mem0Provider(httpClient, options: new()
        {
            UserId = "U1"
        });

        // Clear out any memories from previous runs, if any, to demonstrate a first run experience.
        await mem0Provider.ClearStoredMemoriesAsync();

        // Create our agent and add our finance plugin with auto function invocation.
        Kernel kernel = this.CreateKernelWithChatCompletion();
        kernel.Plugins.AddFromType<FinancePlugin>();
        ChatCompletionAgent agent =
            new()
            {
                Name = AgentName,
                Instructions = AgentInstructions,
                Kernel = kernel,
                Arguments = new KernelArguments(new PromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() })
            };

        Console.WriteLine("----- First Conversation -----");

        // Create a thread for the agent and add the mem0 component to it.
        ChatHistoryAgentThread agentThread = new();
        agentThread.AIContextProviders.Add(mem0Provider);

        // First ask the agent to retrieve a company report with no previous context.
        // The agent will not be able to invoke the plugin, since it doesn't know
        // the company code or the report format, so it should ask for clarification.
        string userMessage = "Please retrieve my company report";
        Console.WriteLine($"User: {userMessage}");

        ChatMessageContent message = await agent.InvokeAsync(userMessage, agentThread).FirstAsync();
        Console.WriteLine($"Assistant:\n{message.Content}");

        // Now tell the agent the company code and the report format that you want to use
        // and it should be able to invoke the plugin and return the report.
        userMessage = "I always work with CNTS and I always want a detailed report format";
        Console.WriteLine($"User: {userMessage}");

        message = await agent.InvokeAsync(userMessage, agentThread).FirstAsync();
        Console.WriteLine($"Assistant:\n{message.Content}");

        Console.WriteLine("----- Second Conversation -----");

        // Create a new thread for the agent and add our mem0 component to it again
        // The new thread has no context of the previous conversation.
        agentThread = new();
        agentThread.AIContextProviders.Add(mem0Provider);

        // Since we have the mem0 component in the thread, the agent should be able to
        // retrieve the company report without asking for clarification, as it will
        // be able to remember the user preferences from the last thread.
        userMessage = "Please retrieve my company report";
        Console.WriteLine($"User: {userMessage}");

        message = await agent.InvokeAsync(userMessage, agentThread).FirstAsync();
        Console.WriteLine($"Assistant:\n{message.Content}");
    }

    private sealed class FinancePlugin
    {
        [KernelFunction]
        public string RetrieveCompanyReport(string companyCode, ReportFormat reportFormat)
        {
            if (companyCode != "CNTS")
            {
                throw new ArgumentException("Company code not found");
            }

            return reportFormat switch
            {
                ReportFormat.Brief => "CNTS is a company that specializes in technology.",
                ReportFormat.Detailed => "CNTS is a company that specializes in technology. It had a revenue of $10 million in 2022. It has 100 employees.",
                _ => throw new ArgumentException("Report format not found")
            };
        }
    }

    private enum ReportFormat
    {
        Brief,
        Detailed
    }
}

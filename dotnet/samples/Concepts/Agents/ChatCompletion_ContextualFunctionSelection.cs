// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Functions;
using ModelContextProtocol.Client;

namespace Agents;

#pragma warning disable SKEXP0130 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

/// <summary>
/// Demonstrate creation of <see cref="ChatCompletionAgent"/> and
/// adding contextual function selection capabilities to it.
/// </summary>
public class ChatCompletion_ContextualFunctionSelection(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Shows how to configure agent to use <see cref="ContextualFunctionProvider"/>
    /// to enable contextual function selection.
    /// </summary>
    [Fact]
    private async Task SelectFunctionsRelevantToContext()
    {
        var embeddingGenerator = new AzureOpenAIClient(new Uri(TestConfiguration.AzureOpenAIEmbeddings.Endpoint), new AzureCliCredential())
            .GetEmbeddingClient(TestConfiguration.AzureOpenAIEmbeddings.DeploymentName)
            .AsIEmbeddingGenerator(1536);

        // Create our agent.
        Kernel kernel = this.CreateKernelWithChatCompletion();
        ChatCompletionAgent agent =
            new()
            {
                Name = "GithubAssistant",
                Instructions = "You are a friendly assistant that helps with GitHub-related tasks. " +
                               "For each response, list available functions",
                Kernel = kernel,
                Arguments = new(new PromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(options: new FunctionChoiceBehaviorOptions { RetainArgumentTypes = true }) })
            };

        // Create MCP client to access GitHub server.
        await using IMcpClient mcpClient = await CreateClientForGitHubMCPServerAsync();

        // Retrieve the list of tools available to work with GitHub.
        var gitHubMcpTools = await mcpClient.ListToolsAsync();

        // Create a thread and register context based function selection provider that will do RAG on
        // provided functions to advertise only those that are relevant to the current context.
        ChatHistoryAgentThread agentThread = new();

        agentThread.AIContextProviders.Add(
            new ContextualFunctionProvider(
                inMemoryVectorStore: new InMemoryVectorStore(new InMemoryVectorStoreOptions() { EmbeddingGenerator = embeddingGenerator }),
                vectorDimensions: 1536,
                options: new()
                {
                    // Selecting top three relevant functions.
                    MaxNumberOfFunctions = 3,

                    // Use the last user message as context as relevant functions might be required to answer it.
                    ContextEmbeddingValueProvider = (messages, _) => Task.FromResult(messages.Last(m => m.Role == ChatRole.User).Text)
                },
                functions: [.. gitHubMcpTools]
            )
        );

        // Invoke and display assistant response
        ChatMessageContent message = await agent.InvokeAsync("Get the two latest pull requests from the microsoft/semantic-kernel GitHub repository.", agentThread).FirstAsync();
        Console.WriteLine(message.Content);

        //Expected output:
        /*
            Here are the two latest pull requests from the `microsoft/semantic-kernel` GitHub repository:
            1. **Pull Request #12224**
               - **Title:** Python: Use BaseModel instead of KernelBaseModel in samples
               - **State:** Open
               - **Created At:** May 21, 2025
               - **Link:** [View Pull Request](https://github.com/microsoft/semantic-kernel/pull/12224)
            2. **Pull Request #12221**
               - **Title:** .Net: Remove Kusto and DuckDB
               - **User:** [westey-m](https://github.com/westey-m)
               - **State:** Open
               - **Created At:** May 21, 2025
               - **Link:** [View Pull Request](https://github.com/microsoft/semantic-kernel/pull/12221)

            If you need any more information or assistance, feel free to ask!

            ### Available Functions
            - List and filter repository pull requests
            - Get the list of files changed in a pull request
            - Search for issues and pull requests across GitHub repositories
        */
    }

    private static async Task<IMcpClient> CreateClientForGitHubMCPServerAsync()
    {
        return await McpClientFactory.CreateAsync(new StdioClientTransport(new()
        {
            Command = "npx",
            Arguments = ["-y", "@modelcontextprotocol/server-github"],
        }));
    }
}

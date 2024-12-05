using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AI.Bedrock;
using Microsoft.SemanticKernel.Memory;
using Microsoft.Extensions.Configuration;
using OpenSearch.Client;

public class BedrockRAGExample
{
    private readonly IKernel _kernel;
    private readonly ISemanticTextMemory _memory;
    private readonly string _openSearchEndpoint;
    private readonly string _embeddingModel;

    public BedrockRAGExample(IConfiguration configuration)
    {
        // Load configuration
        _openSearchEndpoint = configuration["AWSBedrockSettings:OpenSearchEndpoint"]!;
        _embeddingModel = configuration["AWSBedrockSettings:EmbeddingModel"]!;
        var modelId = configuration["AWSBedrockSettings:ModelId"]!;

        // Initialize OpenSearch client
        var openSearchSettings = new ConnectionSettings(new Uri(_openSearchEndpoint))
            .DefaultIndex("semantic-kernel-memories");
        var openSearchClient = new OpenSearchClient(openSearchSettings);

        // Initialize the kernel with AWS Bedrock
        _kernel = Kernel.Builder
            .WithAWSBedrockChatCompletion(modelId)
            .WithAWSBedrockTextEmbeddingGeneration(_embeddingModel)
            .Build();

        // Initialize memory with OpenSearch
        _memory = new MemoryBuilder()
            .WithOpenSearchMemoryStore(openSearchClient)
            .WithAWSBedrockTextEmbeddingGeneration(_embeddingModel)
            .Build();
    }

    public async Task RunRAGExampleAsync()
    {
        Console.WriteLine("Running RAG example with AWS Bedrock and OpenSearch...\n");

        // First, let's add some documents to our knowledge base
        await AddDocumentsToMemoryAsync();

        // Now let's query the knowledge base
        await QueryKnowledgeBaseAsync("What are the key features of Semantic Kernel?");
        await QueryKnowledgeBaseAsync("How does RAG work with AWS Bedrock?");
    }

    private async Task AddDocumentsToMemoryAsync()
    {
        var documents = new List<(string id, string text)>
        {
            ("doc1", "Semantic Kernel is an SDK that integrates Large Language Models (LLMs) with conventional programming languages. " +
                    "It combines natural language semantic functions with traditional code functions, making AI orchestration simple and efficient."),

            ("doc2", "RAG (Retrieval Augmented Generation) is a pattern that enhances LLM responses by providing relevant context from a knowledge base. " +
                    "It first retrieves relevant documents using semantic search, then uses these documents to augment the prompt sent to the LLM."),

            ("doc3", "AWS Bedrock provides a unified API for accessing various foundation models. " +
                    "It supports models like Claude from Anthropic and Titan from Amazon, offering features such as text generation, embeddings, and image generation.")
        };

        foreach (var (id, text) in documents)
        {
            await _memory.SaveInformationAsync(
                collection: "semantic-kernel-docs",
                text: text,
                id: id);
        }

        Console.WriteLine("Documents added to memory.\n");
    }

    private async Task QueryKnowledgeBaseAsync(string query)
    {
        Console.WriteLine($"User Query: {query}\n");

        // Search for relevant memories
        var searchResults = _memory.SearchAsync(
            collection: "semantic-kernel-docs",
            query: query,
            limit: 2);

        var relevantContext = new List<string>();
        await foreach (var result in searchResults)
        {
            relevantContext.Add(result.Metadata.Text);
        }

        // Create a prompt that includes the retrieved context
        var prompt = @$"
            Use the following context to answer the question. Be specific and use information from the context.
            If you cannot answer based on the context, say so.

            Context:
            {string.Join("\n", relevantContext)}

            Question: {query}";

        try
        {
            // Get completion from Bedrock
            var result = await _kernel.InvokePromptAsync(prompt);
            Console.WriteLine($"Assistant: {result.GetValue<string>()}\n");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error: {ex.Message}\n");
        }
    }

    public static async Task Main()
    {
        IConfiguration configuration = new ConfigurationBuilder()
            .SetBasePath(Directory.GetCurrentDirectory())
            .AddJsonFile("appsettings.json", optional: false)
            .Build();

        var example = new BedrockRAGExample(configuration);
        await example.RunRAGExampleAsync();
    }
}
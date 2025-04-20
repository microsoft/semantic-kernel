// Copyright (c) Microsoft. All rights reserved.

using MCPServer;
using MCPServer.ProjectResources;
using MCPServer.Prompts;
using MCPServer.Resources;
using MCPServer.Tools;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Embeddings;
using ModelContextProtocol.Protocol.Types;
using ModelContextProtocol.Server;

var builder = Host.CreateEmptyApplicationBuilder(settings: null);

// Load and validate configuration
(string embeddingModelId, string chatModelId, string apiKey) = GetConfiguration();

// Register the kernel
IKernelBuilder kernelBuilder = builder.Services.AddKernel();

// Register SK plugins
kernelBuilder.Plugins.AddFromType<DateTimeUtils>();
kernelBuilder.Plugins.AddFromType<WeatherUtils>();
kernelBuilder.Plugins.AddFromType<MailboxUtils>();

// Register SK agent as plugin
kernelBuilder.Plugins.AddFromFunctions("Agents", [AgentKernelFunctionFactory.CreateFromAgent(CreateSalesAssistantAgent(chatModelId, apiKey))]);

// Register embedding generation service and in-memory vector store
kernelBuilder.Services.AddSingleton<IVectorStore, InMemoryVectorStore>();
kernelBuilder.Services.AddOpenAITextEmbeddingGeneration(embeddingModelId, apiKey);

// Register MCP server
builder.Services
    .AddMcpServer()
    .WithStdioServerTransport()

    // Add all functions from the kernel plugins to the MCP server as tools
    .WithTools()

    // Register the `getCurrentWeatherForCity` prompt
    .WithPrompt(PromptDefinition.Create(EmbeddedResource.ReadAsString("getCurrentWeatherForCity.json")))

    // Register vector search as MCP resource template
    .WithResourceTemplate(CreateVectorStoreSearchResourceTemplate())

    // Register the cat image as a MCP resource
    .WithResource(ResourceDefinition.CreateBlobResource(
        uri: "image://cat.jpg",
        name: "cat-image",
        content: EmbeddedResource.ReadAsBytes("cat.jpg"),
        mimeType: "image/jpeg"));

await builder.Build().RunAsync();

/// <summary>
/// Gets configuration.
/// </summary>
static (string EmbeddingModelId, string ChatModelId, string ApiKey) GetConfiguration()
{
    // Load and validate configuration
    IConfigurationRoot config = new ConfigurationBuilder()
        .AddUserSecrets<Program>()
        .AddEnvironmentVariables()
        .Build();

    if (config["OpenAI:ApiKey"] is not { } apiKey)
    {
        const string Message = "Please provide a valid OpenAI:ApiKey to run this sample. See the associated README.md for more details.";
        Console.Error.WriteLine(Message);
        throw new InvalidOperationException(Message);
    }

    string embeddingModelId = config["OpenAI:EmbeddingModelId"] ?? "text-embedding-3-small";

    string chatModelId = config["OpenAI:ChatModelId"] ?? "gpt-4o-mini";

    return (embeddingModelId, chatModelId, apiKey);
}
static ResourceTemplateDefinition CreateVectorStoreSearchResourceTemplate(Kernel? kernel = null)
{
    return new ResourceTemplateDefinition
    {
        Kernel = kernel,
        ResourceTemplate = new()
        {
            UriTemplate = "vectorStore://{collection}/{prompt}",
            Name = "Vector Store Record Retrieval",
            Description = "Retrieves relevant records from the vector store based on the provided prompt."
        },
        Handler = async (
            RequestContext<ReadResourceRequestParams> context,
            string collection,
            string prompt,
            [FromKernelServices] ITextEmbeddingGenerationService embeddingGenerationService,
            [FromKernelServices] IVectorStore vectorStore,
            CancellationToken cancellationToken) =>
        {
            // Get the vector store collection
            IVectorStoreRecordCollection<Guid, TextDataModel> vsCollection = vectorStore.GetCollection<Guid, TextDataModel>(collection);

            // Check if the collection exists, if not create and populate it
            if (!await vsCollection.CollectionExistsAsync(cancellationToken))
            {
                static TextDataModel CreateRecord(string text, ReadOnlyMemory<float> embedding)
                {
                    return new()
                    {
                        Key = Guid.NewGuid(),
                        Text = text,
                        Embedding = embedding
                    };
                }

                string content = EmbeddedResource.ReadAsString("semantic-kernel-info.txt");

                // Create a collection from the lines in the file
                await vectorStore.CreateCollectionFromListAsync<Guid, TextDataModel>(collection, content.Split('\n'), embeddingGenerationService, CreateRecord);
            }

            // Generate embedding for the prompt
            ReadOnlyMemory<float> promptEmbedding = await embeddingGenerationService.GenerateEmbeddingAsync(prompt, cancellationToken: cancellationToken);

            // Retrieve top three matching records from the vector store
            VectorSearchResults<TextDataModel> result = await vsCollection.VectorizedSearchAsync(promptEmbedding, new() { Top = 3 }, cancellationToken);

            // Return the records as resource contents
            List<ResourceContents> contents = [];

            await foreach (var record in result.Results)
            {
                contents.Add(new TextResourceContents()
                {
                    Text = record.Record.Text,
                    Uri = context.Params!.Uri!,
                    MimeType = "text/plain",
                });
            }

            return new ReadResourceResult { Contents = contents };
        }
    };
}

static Agent CreateSalesAssistantAgent(string chatModelId, string apiKey)
{
    IKernelBuilder kernelBuilder = Kernel.CreateBuilder();

    // Register the SK plugin for the agent to use
    kernelBuilder.Plugins.AddFromType<OrderProcessingUtils>();

    // Register chat completion service
    kernelBuilder.Services.AddOpenAIChatCompletion(chatModelId, apiKey);

    // Using a dedicated kernel with the `OrderProcessingUtils` plugin instead of the global kernel has a few advantages:
    // - The agent has access to only relevant plugins, leading to better decision-making regarding which plugin to use.
    //   Fewer plugins mean less ambiguity in selecting the most appropriate one for a given task.
    // - The plugin is isolated from other plugins exposed by the MCP server. As a result the client's Agent/AI model does
    //   not have access to irrelevant plugins.
    Kernel kernel = kernelBuilder.Build();

    // Define the agent
    return new ChatCompletionAgent()
    {
        Name = "SalesAssistant",
        Instructions = "You are a sales assistant. Place orders for items the user requests and handle refunds.",
        Description = "Agent to invoke to place orders for items the user requests and handle refunds.",
        Kernel = kernel,
        Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
    };
}

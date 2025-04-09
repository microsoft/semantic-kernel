// Copyright (c) Microsoft. All rights reserved.

using MCPServer;
using MCPServer.Prompts;
using MCPServer.Resources;
using MCPServer.Tools;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Embeddings;
using ModelContextProtocol.Protocol.Types;
using ModelContextProtocol.Server;

// Create a kernel with embedding generation service and in-memory vector store
Kernel kernel = CreateKernel();

// Register plugins
kernel.Plugins.AddFromType<DateTimeUtils>();
kernel.Plugins.AddFromType<WeatherUtils>();

var builder = Host.CreateEmptyApplicationBuilder(settings: null);
builder.Services
    .AddMcpServer()
    .WithStdioServerTransport()

    // Add all functions from the kernel plugins to the MCP server as tools
    .WithTools(kernel.Plugins)

    // Register the `getCurrentWeatherForCity` prompt
    .WithPrompt(PromptDefinition.Create(EmbeddedResource.ReadAsString("Prompts.getCurrentWeatherForCity.json"), kernel))

    // Register vector search as MCP resource template
    .WithResourceTemplate(CreateVectorStoreSearchResourceTemplate(kernel))

    // Register the cat image as a MCP resource
    .WithResource(ResourceDefinition.CreateBlobResource(
        kernel: kernel,
        uri: "image://cat.jpg",
        name: "cat-image",
        content: EmbeddedResource.ReadAsBytes("Resources.cat.jpg"),
        mimeType: "image/jpeg"));

await builder.Build().RunAsync();

/// <summary>
/// Creates an instance of <see cref="Kernel"/> with AI services.
/// </summary>
/// <returns>An instance of <see cref="Kernel"/>.</returns>
static Kernel CreateKernel()
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

    string modelId = config["OpenAI:EmbeddingModelId"] ?? "text-embedding-3-small";

    IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
    kernelBuilder.Services.AddOpenAITextEmbeddingGeneration(modelId: modelId, apiKey: apiKey);
    kernelBuilder.Services.AddSingleton<IVectorStore, InMemoryVectorStore>();

    return kernelBuilder.Build();
}

static ResourceTemplateDefinition CreateVectorStoreSearchResourceTemplate(Kernel kernel)
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
            [FromKernelServicesAttribute] ITextEmbeddingGenerationService embeddingGenerationService,
            [FromKernelServicesAttribute] IVectorStore vectorStore,
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

                string content = EmbeddedResource.ReadAsString("Resources.semantic-kernel-info.txt");

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

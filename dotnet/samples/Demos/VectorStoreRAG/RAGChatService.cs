// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using VectorStoreRAG.Options;

namespace VectorStoreRAG;

/// <summary>
/// Main service class for the application.
/// </summary>
/// <typeparam name="TKey">The type of the data model key.</typeparam>
/// <param name="dataLoader">Used to load data into the vector store.</param>
/// <param name="vectorStoreTextSearch">Used to search the vector store.</param>
/// <param name="kernel">Used to make requests to the LLM.</param>
/// <param name="ragConfigOptions">The configuration options for the application.</param>
internal class RAGChatService<TKey>(
    IDataLoader dataLoader,
    VectorStoreTextSearch<TextSnippet<TKey>> vectorStoreTextSearch,
    Kernel kernel,
    IOptions<RagConfig> ragConfigOptions) : IHostedService
{
    private Task? _dataLoaded;
    private Task? _chatLoop;

    public Task StartAsync(CancellationToken cancellationToken)
    {
        // Start to load all the configured PDFs into the vector store.
        this._dataLoaded = this.LoadDataAsync(cancellationToken);

        // Start the chat loop.
        this._chatLoop = this.ChatLoopAsync(cancellationToken);

        return Task.CompletedTask;
    }

    public Task StopAsync(CancellationToken cancellationToken)
    {
        return Task.CompletedTask;
    }

    private async Task ChatLoopAsync(CancellationToken cancellationToken)
    {
        // Wait for the data to be loaded before starting the chat loop.
        while (this._dataLoaded != null && !this._dataLoaded.IsCompleted && !cancellationToken.IsCancellationRequested)
        {
            await Task.Delay(1_000, cancellationToken).ConfigureAwait(false);
        }

        // If data loading failed, don't start the chat loop.
        if (this._dataLoaded != null && this._dataLoaded.IsFaulted)
        {
            Console.WriteLine("Failed to load data");
            return;
        }

        Console.WriteLine("PDF loading complete\n");

        // Add a search plugin to the kernel which we will use in the template below
        // to do a vector search for related information to the user query.
        kernel.Plugins.Add(vectorStoreTextSearch.CreateWithGetTextSearchResults("SearchPlugin"));

        // Start the chat loop.
        while (!cancellationToken.IsCancellationRequested)
        {
            // Prompt the user for a question.
            Console.ForegroundColor = ConsoleColor.Green;
            Console.WriteLine("Assistant > What would you like to know from the PDFs?");

            // Read the user question.
            Console.ForegroundColor = ConsoleColor.White;
            Console.Write("User > ");
            var question = Console.ReadLine();

            // Invoke the LLM with a template, that uses the search plugin to get related information
            // to the user query from the vector store and add it to the LLM prompt.
            var response = kernel.InvokePromptStreamingAsync(
                promptTemplate: """
                    Please use this information to answer the question:
                    {{#with (SearchPlugin-GetTextSearchResults question)}}  
                      {{#each this}}  
                        Name: {{Name}}
                        Value: {{Value}}
                        Link: {{Link}}
                        -----------------
                      {{/each}}  
                    {{/with}}  
                    
                    Question: {{question}}
                    """,
                arguments: new KernelArguments()
                {
                    { "question", question },
                },
                templateFormat: "handlebars",
                promptTemplateFactory: new HandlebarsPromptTemplateFactory(),
                cancellationToken: cancellationToken);

            // Stream the LLM response to the console.
            Console.ForegroundColor = ConsoleColor.Green;
            Console.Write("\nAssistant > ");
            await foreach (var message in response.ConfigureAwait(false))
            {
                Console.Write(message);
            }
            Console.WriteLine();
        }
    }

    /// <summary>
    /// Load all configured PDFs into the vector store.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    /// <returns>An async task that completes when the loading is complete.</returns>
    private async Task LoadDataAsync(CancellationToken cancellationToken)
    {
        try
        {
            foreach (var pdfFilePath in ragConfigOptions.Value.PdfFilePaths ?? [])
            {
                Console.WriteLine($"Loading PDF into vector store: {pdfFilePath}");
                await dataLoader.LoadPdf(pdfFilePath, cancellationToken).ConfigureAwait(false);
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Failed to load PDFs: {ex.Message}");
            throw;
        }
    }
}

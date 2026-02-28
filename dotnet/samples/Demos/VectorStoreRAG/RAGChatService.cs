// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
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
/// <param name="appShutdownCancellationTokenSource">Used to gracefully shut down the entire application when cancelled.</param>
internal sealed class RAGChatService<TKey>(
    IDataLoader dataLoader,
    VectorStoreTextSearch<TextSnippet<TKey>> vectorStoreTextSearch,
    Kernel kernel,
    IOptions<RagConfig> ragConfigOptions,
    [FromKeyedServices("AppShutdown")] CancellationTokenSource appShutdownCancellationTokenSource) : IHostedService
{
    private Task? _dataLoaded;
    private Task? _chatLoop;

    /// <summary>
    /// Start the service.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    /// <returns>An async task that completes when the service is started.</returns>
    public Task StartAsync(CancellationToken cancellationToken)
    {
        // Start to load all the configured PDFs into the vector store.
        if (ragConfigOptions.Value.BuildCollection)
        {
            this._dataLoaded = this.LoadDataAsync(cancellationToken);
        }
        else
        {
            this._dataLoaded = Task.CompletedTask;
        }

        // Start the chat loop.
        this._chatLoop = this.ChatLoopAsync(cancellationToken);

        return Task.CompletedTask;
    }

    /// <summary>
    /// Stop the service.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    /// <returns>An async task that completes when the service is stopped.</returns>
    public Task StopAsync(CancellationToken cancellationToken)
    {
        return Task.CompletedTask;
    }

    /// <summary>
    /// Contains the main chat loop for the application.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    /// <returns>An async task that completes when the chat loop is shut down.</returns>
    private async Task ChatLoopAsync(CancellationToken cancellationToken)
    {
        var pdfFiles = string.Join(", ", ragConfigOptions.Value.PdfFilePaths ?? []);

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

        Console.ForegroundColor = ConsoleColor.Green;
        Console.WriteLine("Assistant > Press enter with no prompt to exit.");

        // Add a search plugin to the kernel which we will use in the template below
        // to do a vector search for related information to the user query.
        kernel.Plugins.Add(vectorStoreTextSearch.CreateWithGetTextSearchResults(top: 5, "SearchPlugin"));

        // Start the chat loop.
        while (!cancellationToken.IsCancellationRequested)
        {
            // Prompt the user for a question.
            Console.ForegroundColor = ConsoleColor.Green;
            Console.WriteLine($"Assistant > What would you like to know from the loaded PDFs: ({pdfFiles})?");

            // Read the user question.
            Console.ForegroundColor = ConsoleColor.White;
            Console.Write("User > ");
            var question = Console.ReadLine();

            // Exit the application if the user didn't type anything.
            if (string.IsNullOrWhiteSpace(question))
            {
                appShutdownCancellationTokenSource.Cancel();
                break;
            }

            // Invoke the LLM with a template that uses the search plugin to
            // 1. get related information to the user query from the vector store
            // 2. add the information to the LLM prompt.
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

                    Include citations to the relevant information where it is referenced in the response.
                    
                    Question: {{question}}
                    """,
                arguments: new KernelArguments()
                {
                    { "question", question },
                },
                templateFormat: "handlebars",
                promptTemplateFactory: new HandlebarsPromptTemplateFactory(),
                cancellationToken: cancellationToken);

            // Stream the LLM response to the console with error handling.
            Console.ForegroundColor = ConsoleColor.Green;
            Console.Write("\nAssistant > ");

            try
            {
                await foreach (var message in response.ConfigureAwait(false))
                {
                    Console.Write(message);
                }
                Console.WriteLine();
            }
            catch (Exception ex)
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine($"Call to LLM failed with error: {ex}");
            }
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
                await dataLoader.LoadPdf(
                    pdfFilePath,
                    ragConfigOptions.Value.DataLoadingBatchSize,
                    ragConfigOptions.Value.DataLoadingBetweenBatchDelayInMilliseconds,
                    cancellationToken).ConfigureAwait(false);
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Failed to load PDFs: {ex}");
            throw;
        }
    }
}

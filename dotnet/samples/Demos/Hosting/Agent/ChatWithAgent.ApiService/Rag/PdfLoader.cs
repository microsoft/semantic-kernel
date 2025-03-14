// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Embeddings;
using UglyToad.PdfPig;
using UglyToad.PdfPig.Content;
using UglyToad.PdfPig.DocumentLayoutAnalysis.PageSegmenter;

namespace ChatWithAgent.ApiService;

/// <summary>
/// Class that loads text from a PDF file into a vector store.
/// </summary>
/// <typeparam name="TKey">The type of the data model key.</typeparam>
/// <param name="uniqueKeyGenerator">A function to generate unique keys with.</param>
/// <param name="vectorStoreRecordCollection">The collection to load the data into.</param>
/// <param name="textEmbeddingGenerationService">The service to use for generating embeddings from the text.</param>
/// <param name="chatCompletionService">The chat completion service to use for generating text from images.</param>
/// <param name="logger">The logger to use for logging.</param>
/// <param name="batchSize">The size of the batches to process the content in.</param>
/// <param name="batchLoadingDelayMilliseconds">The delay between processing each batch.</param>
internal sealed class PdfLoader<TKey>(
    UniqueKeyGenerator<TKey> uniqueKeyGenerator,
    IVectorStoreRecordCollection<TKey, TextSnippet<TKey>> vectorStoreRecordCollection,
    ITextEmbeddingGenerationService textEmbeddingGenerationService,
    IChatCompletionService chatCompletionService,
    ILogger<PdfLoader<TKey>> logger,
    int batchSize,
    int batchLoadingDelayMilliseconds) : IDataLoader where TKey : notnull
{
    /// <inheritdoc/>
    public async Task LoadAsync(Stream content, string fileName, CancellationToken cancellationToken)
    {
        // Create the collection if it doesn't exist.
        await vectorStoreRecordCollection.CreateCollectionIfNotExistsAsync(cancellationToken).ConfigureAwait(false);

        // Load the text and images from the PDF file and split them into batches.
        var sections = this.LoadTextAndImages(content, cancellationToken);
        var batches = sections.Chunk(batchSize);

        // Process each batch of content items.
        foreach (var batch in batches)
        {
            // Convert any images to text.
            var textContentTasks = batch.Select(async content =>
            {
                if (content.Text != null)
                {
                    return content;
                }

                var textFromImage = await ConvertImageToTextWithRetryAsync(
                    chatCompletionService,
                    content.Image!.Value,
                    cancellationToken).ConfigureAwait(false);
                return new RawContent { Text = textFromImage, PageNumber = content.PageNumber };
            });
            var textContent = await Task.WhenAll(textContentTasks).ConfigureAwait(false);

            // Map each paragraph to a TextSnippet and generate an embedding for it.
            var recordTasks = textContent.Select(async content => new TextSnippet<TKey>
            {
                Key = uniqueKeyGenerator.GenerateKey(),
                Text = content.Text,
                ReferenceDescription = $"{fileName}#page={content.PageNumber}",
                TextEmbedding = await textEmbeddingGenerationService.GenerateEmbeddingAsync(content.Text!, cancellationToken: cancellationToken).ConfigureAwait(false)
            });

            // Upsert the records into the vector store.
            var records = await Task.WhenAll(recordTasks).ConfigureAwait(false);

            var upsertedKeys = vectorStoreRecordCollection.UpsertBatchAsync(records, cancellationToken: cancellationToken);

            await foreach (var key in upsertedKeys.ConfigureAwait(false))
            {
                // Consider dropping this logging in favor of the vector store's built-in logging, which will be available under LogLevel.Debug
                // out-of-the-box once the telemetry implementation for vector stores is complete. 
                if (logger.IsEnabled(LogLevel.Information))
                {
                    logger.LogInformation("Upserted record {Key} into VectorDB", key);
                }
            }

            await Task.Delay(batchLoadingDelayMilliseconds, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Read the text and images from each page in the provided PDF file.
    /// </summary>
    /// <param name="content">The pdf file content to read the text and images from.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    /// <returns>The text and images from the pdf file, plus the page number that each is on.</returns>
    private IEnumerable<RawContent> LoadTextAndImages(Stream content, CancellationToken cancellationToken)
    {
        using (PdfDocument document = PdfDocument.Open(content))
        {
            foreach (Page page in document.GetPages())
            {
                if (cancellationToken.IsCancellationRequested)
                {
                    break;
                }

                // Skipping images for now
                //foreach (var image in page.GetImages())
                //{
                //    if (image.TryGetPng(out var png))
                //    {
                //        yield return new RawContent { Image = png, PageNumber = page.Number };
                //    }
                //    else
                //    {
                //        if (logger.IsEnabled(LogLevel.Debug))
                //        {
                //            logger.LogDebug("Unsupported image format on page {Number}", page.Number);
                //        }
                //    }
                //}

                var blocks = DefaultPageSegmenter.Instance.GetBlocks(page.GetWords());
                foreach (var block in blocks)
                {
                    if (cancellationToken.IsCancellationRequested)
                    {
                        break;
                    }

                    yield return new RawContent { Text = block.Text, PageNumber = page.Number };
                }
            }
        }
    }

    /// <summary>
    /// Add a simple retry mechanism to image to text.
    /// </summary>
    /// <param name="chatCompletionService">The chat completion service to use for generating text from images.</param>
    /// <param name="imageBytes">The image to generate the text for.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    /// <returns>The generated text.</returns>
    private static async Task<string> ConvertImageToTextWithRetryAsync(
        IChatCompletionService chatCompletionService,
        ReadOnlyMemory<byte> imageBytes,
        CancellationToken cancellationToken)
    {
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage([
            new TextContent("What’s in this image?"),
            new ImageContent(imageBytes, "image/png"),
        ]);
        var result = await chatCompletionService.GetChatMessageContentsAsync(chatHistory, cancellationToken: cancellationToken).ConfigureAwait(false);
        return string.Join("\n", result.Select(x => x.Content));
    }

    /// <summary>
    /// Private model for returning the content items from a PDF file.
    /// </summary>
    private sealed class RawContent
    {
        public string? Text { get; init; }

        public ReadOnlyMemory<byte>? Image { get; init; }

        public int PageNumber { get; init; }
    }
}

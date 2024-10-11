// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Embeddings;
using UglyToad.PdfPig;
using UglyToad.PdfPig.Content;
using UglyToad.PdfPig.DocumentLayoutAnalysis.PageSegmenter;

namespace VectorStoreRAG;

/// <summary>
/// Class that loads text from a PDF file into a vector store.
/// </summary>
/// <typeparam name="TKey">The type of the data model key.</typeparam>
/// <param name="uniqueKeyGenerator">A function to generate unique keys with.</param>
/// <param name="vectorStoreRecordCollection">The collection to load the data into.</param>
/// <param name="textEmbeddingGenerationService">The service to use for generating embeddings from the text.</param>
internal sealed class DataLoader<TKey>(
    UniqueKeyGenerator<TKey> uniqueKeyGenerator,
    IVectorStoreRecordCollection<TKey, TextSnippet<TKey>> vectorStoreRecordCollection,
    ITextEmbeddingGenerationService textEmbeddingGenerationService) : IDataLoader where TKey : notnull
{
    /// <inheritdoc/>
    public async Task LoadPdf(string pdfPath, CancellationToken cancellationToken)
    {
        // Create the collection if it doesn't exist.
        await vectorStoreRecordCollection.CreateCollectionIfNotExistsAsync(cancellationToken).ConfigureAwait(false);

        // Load the paragraphs from the PDF file and split them into batches.
        var sections = LoadParagraphs(pdfPath, cancellationToken);
        var batches = sections.Chunk(10);

        // Process each batch of paragraphs.
        foreach (var batch in batches)
        {
            // Map each paragraph to a TextSnippet and generate an embedding for it.
            var recordTasks = batch.Select(async section => new TextSnippet<TKey>
            {
                Key = uniqueKeyGenerator.GenerateKey(),
                Text = section.ParagraphText,
                ReferenceDescription = $"{new FileInfo(pdfPath).Name}#page={section.PageNumber}",
                ReferenceLink = $"{new Uri(new FileInfo(pdfPath).FullName).AbsoluteUri}#page={section.PageNumber}",
                TextEmbedding = await textEmbeddingGenerationService.GenerateEmbeddingAsync(section.ParagraphText, cancellationToken: cancellationToken).ConfigureAwait(false)
            });

            // Upsert the records into the vector store.
            var records = await Task.WhenAll(recordTasks).ConfigureAwait(false);
            var upsertedKeys = vectorStoreRecordCollection.UpsertBatchAsync(records, cancellationToken: cancellationToken);
            await foreach (var key in upsertedKeys.ConfigureAwait(false))
            {
                Console.WriteLine($"Upserted record '{key}' into VectorDB");
            }
        }
    }

    /// <summary>
    /// Read the text from each paragraph in the provided PDF file.
    /// </summary>
    /// <param name="pdfPath">The pdf file to read the paragraphs from.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    /// <returns>The paragraphs from the pdf file, plus the page that they are on.</returns>
    private static IEnumerable<(string ParagraphText, int PageNumber)> LoadParagraphs(string pdfPath, CancellationToken cancellationToken)
    {
        using (PdfDocument document = PdfDocument.Open(pdfPath))
        {
            foreach (Page page in document.GetPages())
            {
                if (cancellationToken.IsCancellationRequested)
                {
                    break;
                }

                var blocks = DefaultPageSegmenter.Instance.GetBlocks(page.GetWords());
                foreach (var block in blocks)
                {
                    if (cancellationToken.IsCancellationRequested)
                    {
                        break;
                    }

                    yield return (ParagraphText: block.Text, PageNumber: page.Number);
                }
            }
        }
    }
}

// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using OpenAI;
using OpenAI.Assistants;
using OpenAI.Files;
using OpenAI.VectorStores;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Convenience extensions for <see cref="AssistantClient"/>.
/// </summary>
public static class OpenAIClientExtensions
{
    /// <summary>
    /// Creates a vector store asynchronously.
    /// </summary>
    /// <param name="client">The OpenAI client instance.</param>
    /// <param name="fileIds">The collection of file identifiers to include in the vector store.</param>
    /// <param name="waitUntilCompleted">Indicates whether to wait until the operation is completed.</param>
    /// <param name="storeName">The name of the vector store.</param>
    /// <param name="expirationPolicy">The expiration policy for the vector store.</param>
    /// <param name="chunkingStrategy">The chunking strategy for the vector store.</param>
    /// <param name="metadata">The metadata associated with the vector store.</param>
    /// <param name="cancellationToken">The cancellation token to monitor for cancellation requests.</param>
    /// <returns>The identifier of the created vector store.</returns>
    public static async Task<string> CreateVectorStoreAsync(
        this OpenAIClient client,
        IEnumerable<string> fileIds,
        bool waitUntilCompleted = true,
        string? storeName = null,
        VectorStoreExpirationPolicy? expirationPolicy = null,
        FileChunkingStrategy? chunkingStrategy = null,
        IReadOnlyDictionary<string, string>? metadata = null,
        CancellationToken cancellationToken = default)
    {
        VectorStoreCreationOptions options = new()
        {
            Name = storeName,
            ChunkingStrategy = chunkingStrategy,
            ExpirationPolicy = expirationPolicy,
        };

        options.FileIds.AddRange(fileIds);

        if (metadata != null)
        {
            foreach (KeyValuePair<string, string> item in metadata)
            {
                options.Metadata[item.Key] = item.Value;
            }
        }

        VectorStoreClient vectorStoreClient = client.GetVectorStoreClient();
        CreateVectorStoreOperation result = await vectorStoreClient.CreateVectorStoreAsync(waitUntilCompleted, options, cancellationToken).ConfigureAwait(false);

        return result.VectorStoreId;
    }

    /// <summary>
    /// Deletes a vector store asynchronously.
    /// </summary>
    /// <param name="client">The OpenAI client instance.</param>
    /// <param name="vectorStoreId">The identifier of the vector store to delete.</param>
    /// <param name="cancellationToken">The cancellation token to monitor for cancellation requests.</param>
    /// <returns>A boolean indicating whether the vector store was successfully deleted.</returns>
    public static async Task<bool> DeleteVectorStoreAsync(this OpenAIClient client, string vectorStoreId, CancellationToken cancellationToken = default)
    {
        VectorStoreClient vectorStoreClient = client.GetVectorStoreClient();
        VectorStoreDeletionResult result = await vectorStoreClient.DeleteVectorStoreAsync(vectorStoreId, cancellationToken).ConfigureAwait(false);
        return result.Deleted;
    }

    /// <summary>
    /// Uploads a file to use with the assistant.
    /// </summary>
    /// <param name="client">The OpenAI client instance.</param>
    /// <param name="stream">The content to upload.</param>
    /// <param name="name">The name of the file.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The file identifier.</returns>
    /// <remarks>
    /// Use the <see cref="OpenAIFileClient"/> directly for more advanced file operations.
    /// </remarks>
    public static async Task<string> UploadAssistantFileAsync(this OpenAIClient client, Stream stream, string name, CancellationToken cancellationToken = default)
    {
        OpenAIFileClient fileClient = client.GetOpenAIFileClient();

        OpenAIFile fileInfo = await fileClient.UploadFileAsync(stream, name, FileUploadPurpose.Assistants, cancellationToken).ConfigureAwait(false);

        return fileInfo.Id;
    }

    /// <summary>
    /// Deletes a file asynchronously.
    /// </summary>
    /// <param name="client">The OpenAI client instance.</param>
    /// <param name="fileId">The identifier of the file to delete.</param>
    /// <param name="cancellationToken">The cancellation token to monitor for cancellation requests.</param>
    /// <returns>A boolean indicating whether the file was successfully deleted.</returns>
    public static async Task<bool> DeleteFileAsync(this OpenAIClient client, string fileId, CancellationToken cancellationToken = default)
    {
        OpenAIFileClient fileClient = client.GetOpenAIFileClient();
        FileDeletionResult result = await fileClient.DeleteFileAsync(fileId, cancellationToken).ConfigureAwait(false);
        return result.Deleted;
    }
}

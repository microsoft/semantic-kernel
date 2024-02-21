// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Core;

internal interface IHuggingFaceClient
{
    /// <summary>
    /// Generates text based on the given prompt asynchronously.
    /// </summary>
    /// <param name="prompt">The prompt for generating text content.</param>
    /// <param name="executionSettings">The prompt execution settings (optional).</param>
    /// <param name="cancellationToken">The cancellation token (optional).</param>
    /// <returns>A list of text content generated based on the prompt.</returns>
    Task<IReadOnlyList<TextContent>> GenerateTextAsync(
        string prompt,
        PromptExecutionSettings executionSettings,
        CancellationToken cancellationToken);

    /// <summary>
    /// Streams the generated text content asynchronously.
    /// </summary>
    /// <param name="prompt">The prompt for generating text content.</param>
    /// <param name="executionSettings">The prompt execution settings (optional).</param>
    /// <param name="cancellationToken">The cancellation token (optional).</param>
    /// <returns>An asynchronous enumerable of <see cref="StreamingTextContent"/> streaming text contents.</returns>
    IAsyncEnumerable<StreamingTextContent> StreamGenerateTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Generates an embedding from the given <paramref name="data"/>.
    /// </summary>
    /// <param name="data">List of strings to generate embeddings for</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>List of embeddings</returns>
    Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default);
}

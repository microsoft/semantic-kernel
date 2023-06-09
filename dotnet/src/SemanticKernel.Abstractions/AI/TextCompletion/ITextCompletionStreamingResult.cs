// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.AI.TextCompletion;

[Obsolete("This interface is deprecated and will be removed in one of the next SK SDK versions. Use the ITextStreamingResult interface instead.")]
public interface ITextCompletionStreamingResult : ITextStreamingResult
{
<<<<<<< HEAD
=======
    /// <summary>
    /// Get the streaming text completion from the result.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Current streaming text content for the iteration</returns>
    IAsyncEnumerable<string> GetCompletionStreamingAsync(CancellationToken cancellationToken = default);
>>>>>>> f4e92eb1de8c8e222c51e0fd8e46e0e6be5650b7
}

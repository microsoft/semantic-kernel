// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.AI.TextCompletion;

[Obsolete("This interface is deprecated and will be removed in one of the next SK SDK versions. Use the ITextResult interface instead.")]
public interface ITextCompletionResult : ITextResult
{
<<<<<<< HEAD
=======
    /// <summary>
    /// Gets the model result data.
    /// </summary>
    ModelResult ModelResult { get; }

    /// <summary>
    /// Get the text completion from the result.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Text completion content</returns>
    Task<string> GetCompletionAsync(CancellationToken cancellationToken = default);
>>>>>>> f4e92eb1de8c8e222c51e0fd8e46e0e6be5650b7
}

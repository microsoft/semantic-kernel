// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.AI.TextCompletion;

public interface ITextCompletionResult
{
    /// <summary>
    /// Get the text completion from the result.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Text completion content</returns>
    Task<string> GetCompletionAsync(CancellationToken cancellationToken = default);
}

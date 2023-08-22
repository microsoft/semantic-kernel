// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.AI.TextCompletion;
/// <summary>
/// Interface for text completion results.
/// Example usage:
/// <code>
/// ITextResult textResult = ...;
/// string completion = await textResult.GetCompletionAsync();
/// Console.WriteLine(completion);
/// </code>
/// </summary>
public interface ITextResult
{
    /// <summary>
    /// Gets the model result data.
    /// </summary>
    ModelResult ModelResult { get; }

    /// <summary>
    /// Asynchronously retrieves the text completion result.
    /// </summary>
    /// <param name="cancellationToken">An optional <see cref="CancellationToken"/> to observe while waiting for the task to complete.</param>
    /// <returns>A <see cref="Task{TResult}"/> representing the asynchronous operation, with the result being the completed text.</returns>
    Task<string> GetCompletionAsync(CancellationToken cancellationToken = default);
}

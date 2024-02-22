// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.TextClassification;

/// <summary>
/// Class sponsor that holds extension methods for <see cref ="ITextClassificationService" /> interface.
/// </summary>
[Experimental("SKEXP0006")]
public static class TextClassificationExtensions
{
    /// <summary>
    /// Classify text.
    /// </summary>
    /// <param name="service">The <see cref ="ITextClassificationService" /> service.</param>
    /// <param name="text">The text to classify.</param>
    /// <param name="executionSettings">The AI execution settings (optional).</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Classification of text.</returns>
    [Experimental("SKEXP0006")]
    public static async Task<ClassificationContent> ClassifyTextAsync(
        this ITextClassificationService service,
        string text,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var list = await service.ClassifyTextAsync(new[] { text }, executionSettings, kernel, cancellationToken)
            .ConfigureAwait(false);
        return list.Single();
    }
}

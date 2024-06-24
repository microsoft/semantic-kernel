// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.TextToAudio;

/// <summary>
/// Class with extension methods for <see cref="ITextToAudioService"/> interface.
/// </summary>
[Experimental("SKEXP0001")]
public static class TextToAudioServiceExtensions
{
    /// <summary>
    /// Get audio content from text.
    /// </summary>
    /// <param name="textToAudioService"></param>
    /// <param name="text">The text to generate audio for.</param>
    /// <param name="executionSettings">The AI execution settings (optional).</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Audio content from text.</returns>
    public static async Task<AudioContent> GetAudioContentAsync(
        this ITextToAudioService textToAudioService,
        string text,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
        => (await textToAudioService.GetAudioContentsAsync(text, executionSettings, kernel, cancellationToken).ConfigureAwait(false))
        .Single();
}

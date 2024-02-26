// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.AudioToText;

/// <summary>
/// Class with extension methods for <see cref="IAudioToTextService"/> interface.
/// </summary>
[Experimental("SKEXP0005")]
public static class AudioToTextServiceExtensions
{
    /// <summary>
    /// Get text content from audio content.
    /// </summary>
    /// <param name="audioToTextService">Target <see cref="IAudioToTextService"/> instance.</param>
    /// <param name="content">Audio content.</param>
    /// <param name="executionSettings">The AI execution settings (optional).</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Text content from audio content.</returns>
    public static async Task<TextContent> GetTextContentAsync(
        this IAudioToTextService audioToTextService,
        AudioContent content,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
        => (await audioToTextService.GetTextContentsAsync(content, executionSettings, kernel, cancellationToken).ConfigureAwait(false))
        .Single();
}

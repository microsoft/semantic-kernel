// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Contents;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.TextToAudio;

public interface ITextToAudioService : IAIService
{
    Task<AudioContent> GetAudioContentAsync(
        string text,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default);
}

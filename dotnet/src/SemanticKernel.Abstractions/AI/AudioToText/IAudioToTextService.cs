// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Threading.Tasks;
using System.Threading;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.AudioToText;

public interface IAudioToTextService : IAIService
{
    Task<TextContent> GetTextContentAsync(
        Stream audio,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default);
}

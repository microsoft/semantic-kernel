// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion.TextCompletionResults;

/// <summary>
/// Interface for streaming text completion results in an asynchronous way.
/// </summary>
public interface ITextAsyncStreamingResult : ITextStreamingResult
{
    void AppendResponse(TextCompletionStreamingResponse response);

    void SignalStreamEnd();
}

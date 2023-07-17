// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;

namespace Microsoft.SemanticKernel.AI.TextCompletion;

/// <summary>
/// Interface for text completion streaming results
/// </summary>
public interface ITextStreamingResult : ITextResult
{
    IAsyncEnumerable<string> GetCompletionStreamingAsync(CancellationToken cancellationToken = default);
}

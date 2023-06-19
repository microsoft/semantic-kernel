// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.AI.TextCompletion;

/// <summary>
/// Interface for text completion streaming results
/// </summary>
[Obsolete("This interface is deprecated and will be removed in one of the next SK SDK versions. Use the ITextStreamingResult interface instead.")]
public interface ITextCompletionStreamingResult : ITextStreamingResult
{
}

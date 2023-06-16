// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.AI.TextCompletion;

/// <summary>
/// Interface for text completion results
/// </summary>
[Obsolete("This interface is deprecated and will be removed in one of the next SK SDK versions. Use the ITextResult interface instead.")]
public interface ITextCompletionResult : ITextResult
{
}

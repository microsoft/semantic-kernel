// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.AI.TextCompletion;

public interface ITextCompletionResult
{
    Task<string> GetCompletionAsync(CancellationToken cancellationToken = default);
}

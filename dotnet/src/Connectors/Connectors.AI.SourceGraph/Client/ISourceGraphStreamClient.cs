// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Client;

using Models;


internal interface ISourceGraphStreamClient
{
    Task<CompletionResponse?> CompleteAsync(CompletionsRequest completionsRequest, Action<CompletionResponse>? onPartialResponse = null, CancellationToken cancellationToken = default);
}

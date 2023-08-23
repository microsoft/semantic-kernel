// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Client;

using SemanticKernel.AI.ChatCompletion;
using SemanticKernel.AI.TextCompletion;


public interface ISourceGraphCompletionsClient : IChatCompletion, ITextCompletion
{
}

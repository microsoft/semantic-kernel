// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.Ollama;

internal interface IEndpointProvider
{
    Uri GetTextGenerationEndpoint { get; }
    Uri GetStreamTextGenerationEndpoint { get; }
    Uri GetChatCompletionEndpoint { get; }
    Uri GetStreamChatCompletionEndpoint { get; }
}

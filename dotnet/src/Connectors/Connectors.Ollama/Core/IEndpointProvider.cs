// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.Ollama;

internal interface IEndpointProvider
{
    Uri TextGenerationEndpoint { get; }
    Uri StreamTextGenerationEndpoint { get; }
    Uri ChatCompletionEndpoint { get; }
    Uri StreamChatCompletionEndpoint { get; }
}

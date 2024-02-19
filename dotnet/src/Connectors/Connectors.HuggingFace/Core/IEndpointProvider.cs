// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Core;

internal interface IEndpointProvider
{
    Uri TextGenerationEndpoint { get; }
}

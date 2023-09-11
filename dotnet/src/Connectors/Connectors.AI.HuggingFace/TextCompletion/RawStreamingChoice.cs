// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextCompletion;

internal sealed class RawStreamingChoice : StreamingChoice
{
    public RawStreamingChoice(Stream stream) : base(stream)
    {
    }
}

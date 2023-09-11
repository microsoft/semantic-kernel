// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.SkillDefinition;

internal sealed class NativeStreamingChoice : StreamingChoice
{
    public NativeStreamingChoice(Stream stream) : base(stream)
    {
    }

    public NativeStreamingChoice(string textResult) : base(StreamingSKResult.GetStreamFromString(textResult))
    {
    }
}

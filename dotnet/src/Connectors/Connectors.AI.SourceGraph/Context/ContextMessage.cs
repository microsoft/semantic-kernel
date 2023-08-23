// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Context;

internal class ContextMessage : Message
{
    public FileContext? FileContext { get; set; }

    public ContextMessage(SpeakerType speakerType, string content, FileContext? fileContext = null) : base(speakerType, content) => FileContext = fileContext;

}

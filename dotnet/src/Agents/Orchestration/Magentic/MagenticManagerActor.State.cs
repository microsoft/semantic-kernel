// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Agents.Orchestration.Chat;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Magentic;

internal sealed partial class MagenticManagerActor
{
    private sealed class State(ChatGroup team)
    {
        public string Team { get; } = team.FormatList();
        public string Names { get; } = team.FormatNames();

        public ChatMessageContent? Facts { get; set; }
        public ChatMessageContent? Plan { get; set; }
        public ChatMessageContent? Ledger { get; set; }
    }
}

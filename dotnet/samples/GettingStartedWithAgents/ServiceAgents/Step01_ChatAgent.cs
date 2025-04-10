// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Agents.Template;

namespace GettingStarted.ServiceAgents;

/// <summary>
/// Demonstrate invocation of <see cref="ChatServiceAgent"/>.
/// </summary>
public class Step01_ChatAgent(ITestOutputHelper output)
    : BaseServiceAgentSample<ChatServiceAgent>(output)
{
    protected override string[] Questions =>
        [
            "Hello",
            "Why is the sky blue?",
            "How big is a rainbow?",
            "Thank you"
        ];
}

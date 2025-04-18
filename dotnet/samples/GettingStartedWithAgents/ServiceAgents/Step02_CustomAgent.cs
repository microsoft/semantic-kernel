// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Agents.Template;

namespace GettingStarted.ServiceAgents;

/// <summary>
/// Demonstrate invocation of <see cref="CustomServiceAgent"/>.
/// </summary>
public class Step02_CustomAgent(ITestOutputHelper output)
    : BaseServiceAgentSample<CustomServiceAgent>(output)
{
    protected override string[] Questions =>
        [
            "Why is the sky blue?",
            "How big is a rainbow?",
            "Have you heard of louis wain? he created fantastic cat drawings."
        ];
}

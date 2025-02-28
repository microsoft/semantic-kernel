// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace SemanticKernel.IntegrationTests.TestSettings;

[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Configuration classes are instantiated through IConfiguration.")]
internal sealed class BedrockAgentConfiguration(string agentResourceRoleArn, string foundationModel)
{
    public string AgentResourceRoleArn { get; set; } = agentResourceRoleArn;
    public string FoundationModel { get; set; } = foundationModel;
}

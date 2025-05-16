// Copyright (c) Microsoft. All rights reserved.

using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentWithTextSearchBehaviorConformance;

public class AzureAIAgentWithTextSearchBehaviorTests(ITestOutputHelper output) : AgentWithTextSearchBehavior<AzureAIAgentFixture>(() => new AzureAIAgentFixture(), output)
{
}

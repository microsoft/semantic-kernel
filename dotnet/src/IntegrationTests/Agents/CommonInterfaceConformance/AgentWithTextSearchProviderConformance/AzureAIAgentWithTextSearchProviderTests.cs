// Copyright (c) Microsoft. All rights reserved.

using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentWithTextSearchBehaviorConformance;

public class AzureAIAgentWithTextSearchProviderTests(ITestOutputHelper output) : AgentWithTextSearchProvider<AzureAIAgentFixture>(() => new AzureAIAgentFixture(), output)
{
}

// Copyright (c) Microsoft. All rights reserved.

using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentWithTextSearchBehaviorConformance;

public class OpenAIAssistantAgentWithTextSearchProviderTests(ITestOutputHelper output) : AgentWithTextSearchProvider<OpenAIAssistantAgentFixture>(() => new OpenAIAssistantAgentFixture(), output)
{
}

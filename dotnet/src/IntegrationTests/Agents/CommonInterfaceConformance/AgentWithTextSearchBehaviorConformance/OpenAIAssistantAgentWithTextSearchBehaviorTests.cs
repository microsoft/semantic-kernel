// Copyright (c) Microsoft. All rights reserved.

using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentWithTextSearchBehaviorConformance;

public class OpenAIAssistantAgentWithTextSearchBehaviorTests(ITestOutputHelper output) : AgentWithTextSearchBehavior<OpenAIAssistantAgentFixture>(() => new OpenAIAssistantAgentFixture(), output)
{
}

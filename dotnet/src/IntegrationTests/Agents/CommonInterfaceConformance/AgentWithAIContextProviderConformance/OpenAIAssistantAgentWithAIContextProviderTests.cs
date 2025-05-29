// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentWithStatePartConformance;

public class OpenAIAssistantAgentWithAIContextProviderTests() : AgentWithAIContextProviderTests<OpenAIAssistantAgentFixture>(() => new OpenAIAssistantAgentFixture())
{
}

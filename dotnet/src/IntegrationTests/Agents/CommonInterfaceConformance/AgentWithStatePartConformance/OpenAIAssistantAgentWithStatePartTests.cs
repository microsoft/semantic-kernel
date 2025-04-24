// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentWithStatePartConformance;

public class OpenAIAssistantAgentWithStatePartTests() : AgentWithStatePartTests<OpenAIAssistantAgentFixture>(() => new OpenAIAssistantAgentFixture())
{
}

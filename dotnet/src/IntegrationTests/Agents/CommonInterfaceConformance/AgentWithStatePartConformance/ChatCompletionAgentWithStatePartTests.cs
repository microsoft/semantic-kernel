// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentWithStatePartConformance;

public class ChatCompletionAgentWithStatePartTests() : AgentWithStatePartTests<ChatCompletionAgentFixture>(() => new ChatCompletionAgentFixture())
{
}

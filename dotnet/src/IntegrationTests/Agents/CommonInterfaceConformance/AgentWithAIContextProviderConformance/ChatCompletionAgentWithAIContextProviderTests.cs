// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentWithStatePartConformance;

public class ChatCompletionAgentWithAIContextProviderTests() : AgentWithAIContextProviderTests<ChatCompletionAgentFixture>(() => new ChatCompletionAgentFixture())
{
}

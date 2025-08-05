// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentWithStatePartConformance;

public class OpenAIResponseAgentStoreEnabledWithAIContextProviderTests() : AgentWithAIContextProviderTests<OpenAIResponseAgentFixture>(() => new OpenAIResponseAgentFixture(true))
{
}

public class OpenAIResponseAgentStoreDisabledWithAIContextProviderTests() : AgentWithAIContextProviderTests<OpenAIResponseAgentFixture>(() => new OpenAIResponseAgentFixture(false))
{
}

// Copyright (c) Microsoft. All rights reserved.

using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentWithTextSearchBehaviorConformance;

public class ChatCompletionAgentWithTextSearchProviderTests(ITestOutputHelper output) : AgentWithTextSearchProvider<ChatCompletionAgentFixture>(() => new ChatCompletionAgentFixture(), output)
{
}

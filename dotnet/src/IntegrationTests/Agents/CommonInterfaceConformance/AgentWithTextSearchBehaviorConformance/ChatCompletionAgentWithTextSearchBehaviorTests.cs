// Copyright (c) Microsoft. All rights reserved.

using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentWithTextSearchBehaviorConformance;

public class ChatCompletionAgentWithTextSearchBehaviorTests(ITestOutputHelper output) : AgentWithTextSearchBehavior<ChatCompletionAgentFixture>(() => new ChatCompletionAgentFixture(), output)
{
}

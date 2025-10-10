// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AIAgentAdapterConformance;

public class OpenAIAssistantAgentAdapterTests() : AIAgentAdapterTests(() => new OpenAIAssistantAgentFixture());

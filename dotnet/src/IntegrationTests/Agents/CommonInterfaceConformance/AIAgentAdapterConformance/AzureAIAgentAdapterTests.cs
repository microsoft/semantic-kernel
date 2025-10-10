// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AIAgentAdapterConformance;

public class AzureAIAgentAdapterTests() : AIAgentAdapterTests(() => new AzureAIAgentFixture());

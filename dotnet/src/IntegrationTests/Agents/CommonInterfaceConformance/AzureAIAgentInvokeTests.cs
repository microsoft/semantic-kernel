// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance;

public class AzureAIAgentInvokeTests() : InvokeTests(() => new AzureAIAgentFixture())
{
}

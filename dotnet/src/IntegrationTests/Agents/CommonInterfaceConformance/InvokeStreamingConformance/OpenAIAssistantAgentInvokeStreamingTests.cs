// Copyright (c) Microsoft. All rights reserved.

using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.InvokeStreamingConformance;

[Collection("Sequential")]
public class OpenAIAssistantAgentInvokeStreamingTests() : InvokeStreamingTests(() => new OpenAIAssistantAgentFixture())
{
}

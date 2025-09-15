// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Agents;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI.Extensions;

/// <summary>
/// Tests for KernelExtensions.
/// </summary>
public class KernelExtensionsTests
{
    /// <summary>
    /// Verify GetOpenAIClientProvider for AzureOpenAI
    /// </summary>
    [Fact]
    public void VerifyGetOpenAIClientProviderForAzureOpenAIWithApiKey()
    {
        // Arrange
        AgentDefinition agentDefinition = new()
        {
            Model = new()
            {
                Id = "gpt-4o-mini",
                Connection = new()
                {
                    ExtensionData = new Dictionary<string, object?>()
                    {
                        ["endpoint"] = "https://contosoo.openai.azure.com",
                        ["api_key"] = "api_key",
                    }
                }
            }
        };

        // Act

        // Assert
    }
}

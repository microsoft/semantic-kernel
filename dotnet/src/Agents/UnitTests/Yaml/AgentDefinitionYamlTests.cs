// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Agents;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Yaml;

/// <summary>
/// Unit tests for <see cref="AgentDefinitionYaml"/>.
/// </summary>
public class AgentDefinitionYamlTests
{
    /// <summary>
    /// Verify can create an instance of <see cref="AgentDefinition"/> from YAML text.
    /// </summary>
    [Fact]
    public void VerifyAgentDefinitionFromYaml()
    {
        // Arrange
        var text =
            """
            id: agent_12345
            version: 1.0.0
            type: chat_completion_agent
            name: My Agent
            description: Description of My Agent
            instructions: Instructions for how My Agent works
            metadata:
                authors:
                    - Bob
                    - Ted
                    - Alice
                tags:
                    - red
                    - green
                    - blue
                created: 2025-02-21
            model:
                id: ${AzureAI:ChatModelId}
                options:
                    temperature: 0.4
                    function_choice_behavior:
                        type: auto
                connection:
                    type: azureai
            inputs:
                input1:
                    description: input1 description
                    required: true
                    default: input1 default
                    sample: input1 sample
                input2:
                    description: input2 description
                    required: false
                    default: input2 default
                    sample: input2 sample
            outputs:
                output1:
                    description: output1 description
            template:
                format: liquid
                parser: semantic-kernel
            tools:
                - id: tool1
                  type: code_interpreter
                  description: Code interpreter tool
                - id: tool2
                  type: file_search
                  description: File search tool
            """;

        // Act
        var agentDefinition = AgentDefinitionYaml.FromYaml(text);

        // Assert
        Assert.NotNull(agentDefinition);
    }

    /// <summary>
    /// Verify can create an instance of <see cref="AgentDefinition"/> from YAML text.
    /// </summary>
    [Fact]
    public void VerifyAgentDefinitionMetadataPropertiesFromYaml()
    {
        // Arrange
        var text =
            """
            version: 1.0.0
            type: chat_completion_agent
            name: My Agent
            description: Description of My Agent
            instructions: Instructions for how My Agent works
            metadata:
                authors:
                    - Bob
                    - Ted
                    - Alice
                tags:
                    - red
                    - green
                    - blue
                created: 2025-02-21
            """;

        // Act
        var agentDefinition = AgentDefinitionYaml.FromYaml(text);

        // Assert
        Assert.NotNull(agentDefinition);
        Assert.Equal("1.0.0", agentDefinition.Version);
        Assert.Equal("chat_completion_agent", agentDefinition.Type);
        Assert.Equal("My Agent", agentDefinition.Name);
        Assert.Equal("Description of My Agent", agentDefinition.Description);
        Assert.Equal("Instructions for how My Agent works", agentDefinition.Instructions);
        Assert.NotNull(agentDefinition.Metadata);
        Assert.Equal(3, agentDefinition.Metadata.Authors?.Count);
        Assert.Equal(3, agentDefinition.Metadata.Tags?.Count);
        Assert.Equal("2025-02-21", agentDefinition.Metadata.ExtensionData["created"]);
    }

    /// <summary>
    /// Verify can create an instance of <see cref="AgentDefinition"/> from YAML text
    /// and values are resolved successfully from an <see cref="IConfiguration"/> instance.
    /// </summary>
    [Fact]
    public void VerifyAgentDefinitionWithConfigurationFromYaml()
    {
        // Arrange
        var text =
            """
            version: 1.0.0
            type: chat_completion_agent
            name: ${OpenAI:AgentName}
            description: Description of My Agent
            instructions: Instructions for how My Agent works
            model:
                id: ${BedrockAgent:ChatModelId}
                connection:
                    connection_string: ${AzureAI.ConnectionString}
                    agent_resource_role_arn: ${BedrockAgent.AgentResourceRoleArn}
            tools:
              - type: file_search
                description: Grounding with available files.
                options:
                  vector_store_ids:
                    - ${OpenAI:VectorStoreId1}
                    - ${OpenAI:VectorStoreId2}
              - type: knowledge_base
                description: You will find information here.
                options:
                  knowledge_base_id: ${BedrockAgent.KnowledgeBaseId}
              - type: bing_grounding
                options:
                  tool_connections:
                    - ${AzureAI.BingConnectionId}
            """;

        var configData = new Dictionary<string, string?>
        {
            {"OpenAI:AgentName", "My Agent"},
            {"OpenAI:VectorStoreId1", "VECTOR-STORE-ID-1"},
            {"OpenAI:VectorStoreId2", "VECTOR-STORE-ID-2"},
            {"AzureAI.ConnectionString", "CONNECTION-STRING"},
            {"AzureAI.BingConnectionId", "BING-CONNECTION-ID"},
            {"BedrockAgent:ChatModelId", "CHAT-MODEL-ID"},
            {"BedrockAgent.AgentResourceRoleArn", "AGENT-RESOURCE-ROLE-ARN"},
            {"BedrockAgent.KnowledgeBaseId", "KNOWLEDGE-BASE-ID"},
        };
        var configuration = new ConfigurationBuilder().AddInMemoryCollection(configData).Build();

        // Act
        var agentDefinition = AgentDefinitionYaml.FromYaml(text, configuration);

        // Assert
        Assert.NotNull(agentDefinition);
        Assert.Equal("1.0.0", agentDefinition.Version);
        Assert.Equal("chat_completion_agent", agentDefinition.Type);
        Assert.Equal("My Agent", agentDefinition.Name);
        Assert.Equal("Description of My Agent", agentDefinition.Description);
        Assert.Equal("Instructions for how My Agent works", agentDefinition.Instructions);

        Assert.NotNull(agentDefinition.Model);
        Assert.Equal("CHAT-MODEL-ID", agentDefinition.Model.Id);
        Assert.NotNull(agentDefinition.Model.Connection);
        Assert.NotNull(agentDefinition.Model.Connection.ExtensionData);
        Assert.Equal("CONNECTION-STRING", agentDefinition.Model.Connection.ExtensionData["connection_string"]);
        Assert.Equal("AGENT-RESOURCE-ROLE-ARN", agentDefinition.Model.Connection.ExtensionData["agent_resource_role_arn"]);

        Assert.NotNull(agentDefinition.Tools);

        var fileSearch = agentDefinition.GetFirstToolDefinition("file_search");
        Assert.NotNull(fileSearch);
        Assert.NotNull(fileSearch.Options);
        Assert.NotNull(fileSearch.Options!["vector_store_ids"]);
        var vectorStoreIds = fileSearch.Options!["vector_store_ids"] as List<object>;
        Assert.NotNull(vectorStoreIds);
        Assert.Equal("VECTOR-STORE-ID-1", vectorStoreIds[0]);
        Assert.Equal("VECTOR-STORE-ID-2", vectorStoreIds[1]);

        var knowledgeBase = agentDefinition.GetFirstToolDefinition("knowledge_base");
        Assert.NotNull(knowledgeBase);
        Assert.NotNull(knowledgeBase.Options);
        var knowledgeBaseId = knowledgeBase.Options!["knowledge_base_id"] as string;
        Assert.Equal("KNOWLEDGE-BASE-ID", knowledgeBaseId);

        var bingGrounding = agentDefinition.GetFirstToolDefinition("bing_grounding");
        Assert.NotNull(bingGrounding);
        Assert.NotNull(bingGrounding.Options);
        Assert.NotNull(bingGrounding.Options!["tool_connections"]);
        var toolConnections = bingGrounding.Options!["tool_connections"] as List<object>;
        Assert.NotNull(toolConnections);
        Assert.Equal("BING-CONNECTION-ID", toolConnections[0]);
    }
}

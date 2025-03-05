// Copyright (c) Microsoft. All rights reserved.

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
                id: gpt-4o-mini
                options:
                    temperature: 0.4
                    function_choice_behavior:
                        type: auto
                configuration:
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
                - description: output1 description
            template:
                format: liquid
                parser: semantic-kernel
            tools:
                - name: tool1
                  type: code_interpreter
                - name: tool2
                  type: file_search
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
}

// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.ComponentModel;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockAgent;
using Amazon.BedrockAgent.Model;
using Amazon.BedrockAgentRuntime;
using Amazon.BedrockAgentRuntime.Model;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Bedrock;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Bedrock;

/// <summary>
/// Unit testing of <see cref="BedrockAgent"/>.
/// </summary>
public class BedrockAgentTests
{
    private readonly Amazon.BedrockAgent.Model.Agent _agentModel = new()
    {
        AgentId = "1234567890",
        AgentName = "testName",
        Description = "test description",
        Instruction = "Instruction must have at least 40 characters",
    };

    private readonly CreateAgentRequest _createAgentRequest = new()
    {
        AgentName = "testName",
        Description = "test description",
        Instruction = "Instruction must have at least 40 characters",
    };

    /// <summary>
    /// Verify the initialization of <see cref="BedrockAgent"/>.
    /// </summary>
    [Fact]
    public void VerifyBedrockAgentDefinition()
    {
        // Arrange
        var (mockClient, mockRuntimeClient) = this.CreateMockClients();
        BedrockAgent agent = new(this._agentModel, mockClient.Object, mockRuntimeClient.Object);

        // Assert
        this.VerifyAgent(agent);
    }

    /// <summary>
    /// Verify the creation of <see cref="BedrockAgent"/> without specialized settings.
    /// </summary>
    [Fact]
    public async Task VerifyBedrockAgentCreateAsync()
    {
        // Arrange
        var (mockClient, mockRuntimeClient) = this.CreateMockClients();
        var agentModel = await mockClient.Object.CreateAndPrepareAgentAsync(this._createAgentRequest);

        // Act
        var bedrockAgent = new BedrockAgent(agentModel, mockClient.Object, mockRuntimeClient.Object);

        // Assert
        this.VerifyAgent(bedrockAgent);
    }

    /// <summary>
    /// Verify the creation of <see cref="BedrockAgent"/> with action groups.
    /// </summary>
    [Fact]
    public async Task VerifyBedrockAgentCreateWithActionGroupsAsync()
    {
        // Arrange
        var (mockClient, mockRuntimeClient) = this.CreateMockClients();
        // Mock the creation of an agent action group.
        mockClient.Setup(x => x.CreateAgentActionGroupAsync(
            It.IsAny<CreateAgentActionGroupRequest>(),
            default)
        ).ReturnsAsync(new CreateAgentActionGroupResponse());
        // Override the sequence of calls to GetAgentAsync to return the agent status
        // because creating an agent action group will require the agent to be prepared again.
        mockClient.SetupSequence(x => x.GetAgentAsync(
            It.IsAny<GetAgentRequest>(),
            default)
        ).ReturnsAsync(new GetAgentResponse
        {
            Agent = new Amazon.BedrockAgent.Model.Agent()
            {
                AgentId = this._agentModel.AgentId,
                AgentName = this._agentModel.AgentName,
                Description = this._agentModel.Description,
                Instruction = this._agentModel.Instruction,
                AgentStatus = AgentStatus.NOT_PREPARED,
            }
        }).ReturnsAsync(new GetAgentResponse
        {
            Agent = new Amazon.BedrockAgent.Model.Agent()
            {
                AgentId = this._agentModel.AgentId,
                AgentName = this._agentModel.AgentName,
                Description = this._agentModel.Description,
                Instruction = this._agentModel.Instruction,
                AgentStatus = AgentStatus.PREPARING,
            }
        }).ReturnsAsync(new GetAgentResponse
        {
            Agent = new Amazon.BedrockAgent.Model.Agent()
            {
                AgentId = this._agentModel.AgentId,
                AgentName = this._agentModel.AgentName,
                Description = this._agentModel.Description,
                Instruction = this._agentModel.Instruction,
                AgentStatus = AgentStatus.PREPARED,
            }
        }).ReturnsAsync(new GetAgentResponse
        {
            Agent = new Amazon.BedrockAgent.Model.Agent()
            {
                AgentId = this._agentModel.AgentId,
                AgentName = this._agentModel.AgentName,
                Description = this._agentModel.Description,
                Instruction = this._agentModel.Instruction,
                AgentStatus = AgentStatus.PREPARING,
            }
        }).ReturnsAsync(new GetAgentResponse
        {
            Agent = new Amazon.BedrockAgent.Model.Agent()
            {
                AgentId = this._agentModel.AgentId,
                AgentName = this._agentModel.AgentName,
                Description = this._agentModel.Description,
                Instruction = this._agentModel.Instruction,
                AgentStatus = AgentStatus.PREPARED,
            }
        });
        var agentModel = await mockClient.Object.CreateAndPrepareAgentAsync(this._createAgentRequest);

        // Act
        var bedrockAgent = new BedrockAgent(agentModel, mockClient.Object, mockRuntimeClient.Object);
        await bedrockAgent.CreateCodeInterpreterActionGroupAsync();

        // Assert
        this.VerifyAgent(bedrockAgent);
        mockClient.Verify(x => x.CreateAgentActionGroupAsync(
            It.IsAny<CreateAgentActionGroupRequest>(),
            default), Times.Exactly(1));
    }

    /// <summary>
    /// Verify the creation of <see cref="BedrockAgent"/> with a kernel.
    /// </summary>
    [Fact]
    public async Task VerifyBedrockAgentCreateWithKernelAsync()
    {
        // Arrange
        var (mockClient, mockRuntimeClient) = this.CreateMockClients();
        var agentModel = await mockClient.Object.CreateAndPrepareAgentAsync(this._createAgentRequest);

        // Act
        Kernel kernel = new();
        var bedrockAgent = new BedrockAgent(agentModel, mockClient.Object, mockRuntimeClient.Object);
        bedrockAgent.Kernel.Plugins.Add(KernelPluginFactory.CreateFromType<WeatherPlugin>());

        // Assert
        this.VerifyAgent(bedrockAgent);
        Assert.Single(bedrockAgent.Kernel.Plugins);
    }

    /// <summary>
    /// Verify the creation of <see cref="BedrockAgent"/> with kernel arguments.
    /// </summary>
    [Fact]
    public async Task VerifyBedrockAgentCreateWithKernelArgumentsAsync()
    {
        // Arrange
        var (mockClient, mockRuntimeClient) = this.CreateMockClients();
        var agentModel = await mockClient.Object.CreateAndPrepareAgentAsync(this._createAgentRequest);

        // Act
        KernelArguments arguments = new() { { "key", "value" } };
        var bedrockAgent = new BedrockAgent(agentModel, mockClient.Object, mockRuntimeClient.Object)
        {
            Arguments = arguments,
        };

        // Assert
        this.VerifyAgent(bedrockAgent);
        Assert.Single(bedrockAgent.Arguments);
    }

    /// <summary>
    /// Verify the bedrock agent returns the expected channel key.
    /// </summary>
    [Fact]
    public async Task VerifyBedrockAgentChannelKeyAsync()
    {
        // Arrange
        var (mockClient, mockRuntimeClient) = this.CreateMockClients();
        var agentModel = await mockClient.Object.CreateAndPrepareAgentAsync(this._createAgentRequest);

        // Act
        var bedrockAgent = new BedrockAgent(agentModel, mockClient.Object, mockRuntimeClient.Object);

        // Assert
        Assert.Single(bedrockAgent.GetChannelKeys());
    }

    /// <summary>
    /// Verify the InvokeAsync method throws when an incorrect thread type is provided.
    /// </summary>
    /// <returns></returns>
    [Fact]
    public async Task VerifyInvokeWithWrongThreadTypeThrowsAsync()
    {
        var (mockClient, mockRuntimeClient) = this.CreateMockClients();
        var bedrockAgent = new BedrockAgent(this._agentModel, mockClient.Object, mockRuntimeClient.Object);
        var messages = new List<ChatMessageContent>
        {
            new (AuthorRole.User, "Hello, how are you?")
        };
        var agentThread = new Mock<AgentThread>();

        // Act
        await Assert.ThrowsAsync<KernelException>(async () =>
        {
            await foreach (var response in bedrockAgent.InvokeAsync(messages, agentThread.Object, null, default))
            {
            }
        });
    }

    private (Mock<IAmazonBedrockAgent>, Mock<IAmazonBedrockAgentRuntime>) CreateMockClients()
    {
        Mock<IAmazonBedrockAgent> mockClient = new();
        Mock<IAmazonBedrockAgentRuntime> mockRuntimeClient = new();

        mockClient.Setup(x => x.CreateAgentAsync(
            It.IsAny<CreateAgentRequest>(),
            default)
        ).ReturnsAsync(new CreateAgentResponse { Agent = this._agentModel });

        // After a new agent is created, its status will first be CREATING then NOT_PREPARED.
        // Internally, we will prepare the agent for use. During preparation, the agent status
        // will be PREPARING, then finally PREPARED.
        mockClient.SetupSequence(x => x.GetAgentAsync(
            It.IsAny<GetAgentRequest>(),
            default)
        ).ReturnsAsync(new GetAgentResponse
        {
            Agent = new Amazon.BedrockAgent.Model.Agent()
            {
                AgentId = this._agentModel.AgentId,
                AgentName = this._agentModel.AgentName,
                Description = this._agentModel.Description,
                Instruction = this._agentModel.Instruction,
                AgentStatus = AgentStatus.NOT_PREPARED,
            }
        }).ReturnsAsync(new GetAgentResponse
        {
            Agent = new Amazon.BedrockAgent.Model.Agent()
            {
                AgentId = this._agentModel.AgentId,
                AgentName = this._agentModel.AgentName,
                Description = this._agentModel.Description,
                Instruction = this._agentModel.Instruction,
                AgentStatus = AgentStatus.PREPARING,
            }
        }).ReturnsAsync(new GetAgentResponse
        {
            Agent = new Amazon.BedrockAgent.Model.Agent()
            {
                AgentId = this._agentModel.AgentId,
                AgentName = this._agentModel.AgentName,
                Description = this._agentModel.Description,
                Instruction = this._agentModel.Instruction,
                AgentStatus = AgentStatus.PREPARED,
            }
        });

#pragma warning disable CA2000 // Dispose objects before losing scope
        mockRuntimeClient.Setup(x => x.InvokeAgentAsync(
            It.IsAny<InvokeAgentRequest>(),
            It.IsAny<CancellationToken>()))
            .ReturnsAsync(new InvokeAgentResponse() { HttpStatusCode = System.Net.HttpStatusCode.OK });
#pragma warning restore CA2000 // Dispose objects before losing scope

        return (mockClient, mockRuntimeClient);
    }

    private void VerifyAgent(BedrockAgent bedrockAgent)
    {
        Assert.Equal(bedrockAgent.Id, this._agentModel.AgentId);
        Assert.Equal(bedrockAgent.Name, this._agentModel.AgentName);
        Assert.Equal(bedrockAgent.Description, this._agentModel.Description);
        Assert.Equal(bedrockAgent.Instructions, this._agentModel.Instruction);
    }

    private sealed class WeatherPlugin
    {
        [KernelFunction, Description("Provides realtime weather information.")]
        public string Current([Description("The location to get the weather for.")] string location)
        {
            return $"The current weather in {location} is 72 degrees.";
        }
    }
}

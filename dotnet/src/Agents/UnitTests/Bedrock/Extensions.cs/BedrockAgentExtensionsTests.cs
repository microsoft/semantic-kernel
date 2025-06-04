// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Amazon.BedrockAgent;
using Amazon.BedrockAgent.Model;
using Amazon.BedrockAgentRuntime;
using Microsoft.SemanticKernel.Agents.Bedrock;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Bedrock.Extensions;

/// <summary>
/// Unit testing of <see cref="BedrockAgentExtensions"/>.
/// </summary>
public class BedrockAgentExtensionsTests
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
    /// Verify the creation of the agent and the preparation of the agent.
    /// The status of the agent should be checked 3 times based on the setup.
    /// 1: Waiting for the agent to go from CREATING to NOT_PREPARED.
    /// 2: Waiting for the agent to go from NOT_PREPARED to PREPARING.
    /// 3: Waiting for the agent to go from PREPARING to PREPARED.
    /// </summary>
    [Fact]
    public async Task VerifyCreateAndPrepareAgentAsync()
    {
        // Arrange
        var (mockClient, mockRuntimeClient) = this.CreateMockClients();

        // Act
        var agentModel = await mockClient.Object.CreateAndPrepareAgentAsync(this._createAgentRequest);

        // Assert
        mockClient.Verify(x => x.GetAgentAsync(
            It.IsAny<GetAgentRequest>(),
            default), Times.Exactly(3));
    }

    /// <summary>
    /// Verify the modification and preparation of the agent is correctly performed.
    /// The status of the agent should be go through the following states:
    /// PREPARED -> PREPARING -> PREPARED.
    /// </summary>
    [Fact]
    public async Task VerifyAssociateAgentKnowledgeBaseAsync()
    {
        // Arrange
        var (mockClient, mockRuntimeClient) = this.CreateMockClients();
        this.ModifyMockClientGetAgentResponseSequence(mockClient);

        mockClient.Setup(x => x.AssociateAgentKnowledgeBaseAsync(
            It.IsAny<AssociateAgentKnowledgeBaseRequest>(),
            default)
        ).ReturnsAsync(new AssociateAgentKnowledgeBaseResponse());

        // Act
        var agentModel = await mockClient.Object.CreateAndPrepareAgentAsync(this._createAgentRequest);
        var bedrockAgent = new BedrockAgent(agentModel, mockClient.Object, mockRuntimeClient.Object);
        await bedrockAgent.AssociateAgentKnowledgeBaseAsync("testKnowledgeBaseId", "testKnowledgeBaseDescription");

        // Assert
        mockClient.Verify(x => x.GetAgentAsync(
            It.IsAny<GetAgentRequest>(),
            default), Times.Exactly(5));
    }

    /// <summary>
    /// Verify the modification and preparation of the agent is correctly performed.
    /// The status of the agent should be go through the following states:
    /// PREPARED -> PREPARING -> PREPARED.
    /// </summary>
    [Fact]
    public async Task VerifyDisassociateAgentKnowledgeBaseAsync()
    {
        // Arrange
        var (mockClient, mockRuntimeClient) = this.CreateMockClients();
        this.ModifyMockClientGetAgentResponseSequence(mockClient);

        mockClient.Setup(x => x.DisassociateAgentKnowledgeBaseAsync(
            It.IsAny<DisassociateAgentKnowledgeBaseRequest>(),
            default)
        ).ReturnsAsync(new DisassociateAgentKnowledgeBaseResponse());

        // Act
        var agentModel = await mockClient.Object.CreateAndPrepareAgentAsync(this._createAgentRequest);
        var bedrockAgent = new BedrockAgent(agentModel, mockClient.Object, mockRuntimeClient.Object);
        await bedrockAgent.DisassociateAgentKnowledgeBaseAsync("testKnowledgeBaseId");

        // Assert
        mockClient.Verify(x => x.GetAgentAsync(
            It.IsAny<GetAgentRequest>(),
            default), Times.Exactly(5));
    }

    /// <summary>
    /// Verify the modification and preparation of the agent is correctly performed.
    /// The status of the agent should be go through the following states:
    /// PREPARED -> PREPARING -> PREPARED.
    /// </summary>
    [Fact]
    public async Task VerifyCreateCodeInterpreterActionGroupAsync()
    {
        // Arrange
        var (mockClient, mockRuntimeClient) = this.CreateMockClients();
        this.ModifyMockClientGetAgentResponseSequence(mockClient);

        mockClient.Setup(x => x.CreateAgentActionGroupAsync(
            It.IsAny<CreateAgentActionGroupRequest>(),
            default)
        ).ReturnsAsync(new CreateAgentActionGroupResponse());

        // Act
        var agentModel = await mockClient.Object.CreateAndPrepareAgentAsync(this._createAgentRequest);
        var bedrockAgent = new BedrockAgent(agentModel, mockClient.Object, mockRuntimeClient.Object);
        await bedrockAgent.CreateCodeInterpreterActionGroupAsync();

        // Assert
        mockClient.Verify(x => x.GetAgentAsync(
            It.IsAny<GetAgentRequest>(),
            default), Times.Exactly(5));
    }

    /// <summary>
    /// Verify the modification and preparation of the agent is correctly performed.
    /// The status of the agent should be go through the following states:
    /// PREPARED -> PREPARING -> PREPARED.
    /// </summary>
    [Fact]
    public async Task VerifyCreateKernelFunctionActionGroupAsync()
    {
        // Arrange
        var (mockClient, mockRuntimeClient) = this.CreateMockClients();
        this.ModifyMockClientGetAgentResponseSequence(mockClient);

        mockClient.Setup(x => x.CreateAgentActionGroupAsync(
            It.IsAny<CreateAgentActionGroupRequest>(),
            default)
        ).ReturnsAsync(new CreateAgentActionGroupResponse());

        // Act
        var agentModel = await mockClient.Object.CreateAndPrepareAgentAsync(this._createAgentRequest);
        var bedrockAgent = new BedrockAgent(agentModel, mockClient.Object, mockRuntimeClient.Object);
        await bedrockAgent.CreateKernelFunctionActionGroupAsync();

        // Assert
        mockClient.Verify(x => x.GetAgentAsync(
            It.IsAny<GetAgentRequest>(),
            default), Times.Exactly(5));
    }

    /// <summary>
    /// Verify the modification and preparation of the agent is correctly performed.
    /// The status of the agent should be go through the following states:
    /// PREPARED -> PREPARING -> PREPARED.
    /// </summary>
    [Fact]
    public async Task VerifyEnableUserInputActionGroupAsync()
    {
        // Arrange
        var (mockClient, mockRuntimeClient) = this.CreateMockClients();
        this.ModifyMockClientGetAgentResponseSequence(mockClient);

        mockClient.Setup(x => x.CreateAgentActionGroupAsync(
            It.IsAny<CreateAgentActionGroupRequest>(),
            default)
        ).ReturnsAsync(new CreateAgentActionGroupResponse());

        // Act
        var agentModel = await mockClient.Object.CreateAndPrepareAgentAsync(this._createAgentRequest);
        var bedrockAgent = new BedrockAgent(agentModel, mockClient.Object, mockRuntimeClient.Object);
        await bedrockAgent.EnableUserInputActionGroupAsync();

        // Assert
        mockClient.Verify(x => x.GetAgentAsync(
            It.IsAny<GetAgentRequest>(),
            default), Times.Exactly(5));
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

        return (mockClient, mockRuntimeClient);
    }

    /// <summary>
    /// Modify the mock client to return a new sequence of responses for the GetAgentAsync method
    /// that reflect the correct sequence of status change when modifying the agent.
    /// </summary>
    private void ModifyMockClientGetAgentResponseSequence(Mock<IAmazonBedrockAgent> mockClient)
    {
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
    }
}

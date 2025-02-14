// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Threading.Tasks;
using Amazon.BedrockAgent;
using Amazon.BedrockAgent.Model;
using Amazon.BedrockAgentRuntime;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Bedrock;
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

    /// <summary>
    /// Verify the initialization of <see cref="BedrockAgent"/>.
    /// </summary>
    [Fact]
    public void VerifyBedrockAgentDefinition()
    {
        // Arrange
#pragma warning disable Moq1410 // Moq: Set MockBehavior to Strict
        Mock<AmazonBedrockAgentClient> mockClient = new();
        Mock<AmazonBedrockAgentRuntimeClient> mockRuntimeClient = new();
#pragma warning restore Moq1410 // Moq: Set MockBehavior to Strict
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
        CreateAgentRequest createAgentRequest = new()
        {
            AgentName = this._agentModel.AgentName,
            Description = this._agentModel.Description,
            Instruction = this._agentModel.Instruction,
        };

        // Act
        var bedrockAgent = await BedrockAgent.CreateAsync(
            createAgentRequest,
            client: mockClient.Object,
            runtimeClient: mockRuntimeClient.Object);

        // Assert
        this.VerifyAgent(bedrockAgent);
    }

    /// <summary>
    /// Verify the retrieval of <see cref="BedrockAgent"/>.
    /// </summary>
    [Fact]
    public async Task VerifyBedrockAgentRetrieveAsync()
    {
        // Arrange
        var (mockClient, mockRuntimeClient) = this.CreateMockClients();

        // Act
        var bedrockAgent = await BedrockAgent.RetrieveAsync(
            this._agentModel.AgentId,
            client: mockClient.Object,
            runtimeClient: mockRuntimeClient.Object);

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
        mockClient.Setup(x => x.CreateAgentActionGroupAsync(
            It.IsAny<CreateAgentActionGroupRequest>(),
            default)
        ).ReturnsAsync(new CreateAgentActionGroupResponse());

        CreateAgentRequest createAgentRequest = new()
        {
            AgentName = this._agentModel.AgentName,
            Description = this._agentModel.Description,
            Instruction = this._agentModel.Instruction,
        };

        // Act
        var bedrockAgent = await BedrockAgent.CreateAsync(
            createAgentRequest,
            enableCodeInterpreter: true,
            enableKernelFunctions: true,
            enableUserInput: true,
            client: mockClient.Object,
            runtimeClient: mockRuntimeClient.Object);

        // Assert
        this.VerifyAgent(bedrockAgent);
        mockClient.Verify(x => x.CreateAgentActionGroupAsync(
            It.IsAny<CreateAgentActionGroupRequest>(),
            default), Times.Exactly(3));
    }

    /// <summary>
    /// Verify the creation of <see cref="BedrockAgent"/> with a kernel.
    /// </summary>
    [Fact]
    public async Task VerifyBedrockAgentCreateWithKernelAsync()
    {
        // Arrange
        var (mockClient, mockRuntimeClient) = this.CreateMockClients();

        CreateAgentRequest createAgentRequest = new()
        {
            AgentName = this._agentModel.AgentName,
            Description = this._agentModel.Description,
            Instruction = this._agentModel.Instruction,
        };

        // Act
        Kernel kernel = new();
        kernel.Plugins.Add(KernelPluginFactory.CreateFromType<WeatherPlugin>());
        var bedrockAgent = await BedrockAgent.CreateAsync(
            createAgentRequest,
            client: mockClient.Object,
            runtimeClient: mockRuntimeClient.Object,
            kernel: kernel);

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

        CreateAgentRequest createAgentRequest = new()
        {
            AgentName = this._agentModel.AgentName,
            Description = this._agentModel.Description,
            Instruction = this._agentModel.Instruction,
        };

        // Act
        KernelArguments arguments = new() { { "key", "value" } };
        var bedrockAgent = await BedrockAgent.CreateAsync(
            createAgentRequest,
            client: mockClient.Object,
            runtimeClient: mockRuntimeClient.Object,
            defaultArguments: arguments);

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

        CreateAgentRequest createAgentRequest = new()
        {
            AgentName = this._agentModel.AgentName,
            Description = this._agentModel.Description,
            Instruction = this._agentModel.Instruction,
        };

        // Act
        var bedrockAgent = await BedrockAgent.CreateAsync(
            createAgentRequest,
            client: mockClient.Object,
            runtimeClient: mockRuntimeClient.Object);

        // Assert
        Assert.Single(bedrockAgent.GetChannelKeys());
    }

    private (Mock<AmazonBedrockAgentClient>, Mock<AmazonBedrockAgentRuntimeClient>) CreateMockClients()
    {
#pragma warning disable Moq1410 // Moq: Set MockBehavior to Strict
        Mock<AmazonBedrockAgentClient> mockClient = new();
        Mock<AmazonBedrockAgentRuntimeClient> mockRuntimeClient = new();
#pragma warning restore Moq1410 // Moq: Set MockBehavior to Strict

        // After a new agent is created, its status will first be NOT_PREPARED.
        // Internally, we will prepare the agent and its status should be updated to PREPARED.
        mockClient.Setup(x => x.CreateAgentAsync(
            It.IsAny<CreateAgentRequest>(),
            default)
        ).ReturnsAsync(new CreateAgentResponse { Agent = this._agentModel });

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
                AgentStatus = AgentStatus.PREPARED,
            }
        });

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
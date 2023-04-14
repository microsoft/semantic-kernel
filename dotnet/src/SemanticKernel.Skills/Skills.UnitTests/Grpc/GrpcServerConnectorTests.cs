// Copyright (c) Microsoft. All rights reserved.

using Moq;
using Xunit;
using Grpc.Core;
using ReferenceSkill;
using System.Threading.Tasks;

namespace SemanticKernel.Skills.UnitTests.Grpc;

public class GrpcServerConnectorTests
{
    [Fact]
    public async Task InvokeAsync_CallsGetRandomActivityMethod()
    {
        // Arrange
        const string input = "surf";
        const string expectedActivity = "random activity";
        const string serverAddress = "https://localhost:5001";
        var request = new GetRandomActivityRequest { Input = input };

        var mockClient = new Mock<ReferenceSkill.Activity>(MockBehavior.Strict);
        mockClient.Setup(client => client.GetRandomActivityAsync(request, It.IsAny<CallOptions>()))
            .ReturnsAsync(new GetRandomActivityResponse { Activity = expectedActivity });

        var grpcInvoker = new GrpcServerConnector();

        // Act
        var response = await grpcInvoker.InvokeAsync(
            (channel, req, options) => new RandomActivitySkillClient(channel).GetRandomActivityAsync(req, options),
            request,
            serverAddress,
            new CallOptions());

        // Assert
        Assert.Equal(expectedActivity, response.Activity);
        mockClient.Verify(client => client.GetRandomActivityAsync(request, It.IsAny<CallOptions>()), Times.Once);
    }

}

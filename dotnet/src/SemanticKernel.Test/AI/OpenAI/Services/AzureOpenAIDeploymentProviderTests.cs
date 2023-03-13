// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.OpenAI.Clients;
using Microsoft.SemanticKernel.AI.OpenAI.HttpSchema;
using Microsoft.SemanticKernel.AI.OpenAI.Services.Deployments;
using Moq;
using Xunit;
using static Microsoft.SemanticKernel.AI.OpenAI.HttpSchema.AzureDeployments;

namespace SemanticKernelTests.AI.OpenAI.Services;
public class AzureOpenAIDeploymentProviderTests
{
    [Fact]
    public async Task ItReturnsDeploymentNameByModelNameAsync()
    {
        //Arrange
        var deployments = new AzureDeployments();
        deployments.Deployments = new List<AzureDeployment>();
        deployments.Deployments.Add(new AzureDeployment { DeploymentName = "fake-deployment-name", ModelName = "fake-model-name", Status = "succeeded", Type = "deployment" });
        deployments.Deployments.Add(new AzureDeployment { DeploymentName = "another-fake-deployment-name", ModelName = "another-fake-model-name", Status = "succeeded", Type = "deployment" });

        var mockAzureOpenAIServiceClient = new Mock<IAzureOpenAIServiceClient>();
        mockAzureOpenAIServiceClient
            .Setup(sc => sc.GetDeploymentsAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(deployments);

        var sut = new AzureOpenAIDeploymentProvider(mockAzureOpenAIServiceClient.Object, "fake-namespace");

        // Scenario #1 - retrieving deployment form service client and caching it.
        //Act
        var deploymentName = await sut.GetDeploymentNameAsync("fake-model-name", CancellationToken.None);

        //Assert
        Assert.NotNull(deploymentName);
        Assert.Equal("fake-deployment-name", deploymentName);

        //Scenario #2 - retrieving deployment from cache, no call to the service client.
        //Act - getting deployment from cache
        deploymentName = await sut.GetDeploymentNameAsync("fake-model-name", CancellationToken.None);

        //Assert
        Assert.NotNull(deploymentName);
        Assert.Equal("fake-deployment-name", deploymentName);
        mockAzureOpenAIServiceClient.Verify(sc => sc.GetDeploymentsAsync(It.IsAny<CancellationToken>()), Times.Once);
    }
}

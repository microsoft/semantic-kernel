// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel.Plugins.Grpc.Model;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.Grpc;

public class GrpcOperationExtensionsTests
{
    private readonly GrpcOperationDataContractType _request;

    private readonly GrpcOperationDataContractType _response;

    private readonly GrpcOperation _operation;

    public GrpcOperationExtensionsTests()
    {
        this._request = new GrpcOperationDataContractType("fake-name", []);

        this._response = new GrpcOperationDataContractType("fake-name", []);

        this._operation = new GrpcOperation("fake-service-name", "fake-operation-name", this._response, this._response);
    }

    [Fact]
    public void ThereShouldBeAddressParameter()
    {
        // Act
        var parameters = GrpcOperation.CreateParameters();

        // Assert
        Assert.NotNull(parameters);
        Assert.NotEmpty(parameters);

        var addressParameter = parameters.SingleOrDefault(p => p.Name == "address");
        Assert.NotNull(addressParameter);
        Assert.Equal("Address for gRPC channel to use.", addressParameter.Description);
    }

    [Fact]
    public void ThereShouldBePayloadParameter()
    {
        // Act
        var parameters = GrpcOperation.CreateParameters();

        // Assert
        Assert.NotNull(parameters);
        Assert.NotEmpty(parameters);

        var payloadParameter = parameters.SingleOrDefault(p => p.Name == "payload");
        Assert.NotNull(payloadParameter);
        Assert.Equal("gRPC request message.", payloadParameter.Description);
    }
}

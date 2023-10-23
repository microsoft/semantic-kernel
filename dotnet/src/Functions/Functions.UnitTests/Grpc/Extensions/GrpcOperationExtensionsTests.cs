// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Functions.Grpc.Extensions;
using Microsoft.SemanticKernel.Functions.Grpc.Model;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.Grpc.Extensions;

public class GrpcOperationExtensionsTests
{
    private readonly GrpcOperationDataContractType _request;

    private readonly GrpcOperationDataContractType _response;

    private readonly GrpcOperation _operation;

    public GrpcOperationExtensionsTests()
    {
        this._request = new GrpcOperationDataContractType("fake-name", new List<GrpcOperationDataContractTypeFiled>());

        this._response = new GrpcOperationDataContractType("fake-name", new List<GrpcOperationDataContractTypeFiled>());

        this._operation = new GrpcOperation("fake-service-name", "fake-operation-name", this._response, this._response);
    }

    [Fact]
    public void ThereShouldBeAddressParameter()
    {
        // Act
        var parameters = this._operation.GetParameters();

        // Assert
        Assert.NotNull(parameters);
        Assert.True(parameters.Any());

        var addressParameter = parameters.SingleOrDefault(p => p.Name == "address");
        Assert.NotNull(addressParameter);
        Assert.Equal("Address for gRPC channel to use.", addressParameter.Description);
    }

    [Fact]
    public void ThereShouldBePayloadParameter()
    {
        // Act
        var parameters = this._operation.GetParameters();

        // Assert
        Assert.NotNull(parameters);
        Assert.True(parameters.Any());

        var payloadParameter = parameters.SingleOrDefault(p => p.Name == "payload");
        Assert.NotNull(payloadParameter);
        Assert.Equal("gRPC request message.", payloadParameter.Description);
    }
}

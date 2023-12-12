// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Plugins.OpenApi;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi;

public class RestApiOperationResponseConverterTests
{
    private readonly RestApiOperationResponseConverter _sut;

    public RestApiOperationResponseConverterTests()
    {
        this._sut = new RestApiOperationResponseConverter();
    }

    [Fact]
    public void ItShouldConvertStringContentToString()
    {
        //Arrange
        var response = new RestApiOperationResponse("fake-content", "fake-content-type");

        //Act
        var result = this._sut.ConvertToString(response);

        //Assert
        Assert.Equal("fake-content", result);
    }

    [Fact]
    public void ItShouldConvertByteContentToString()
    {
        //Arrange
        var response = new RestApiOperationResponse(new byte[] { 00, 01, 02 }, "fake-content-type");

        //Act
        var result = this._sut.ConvertToString(response);

        //Assert
        Assert.Equal("AAEC", result);
    }
}

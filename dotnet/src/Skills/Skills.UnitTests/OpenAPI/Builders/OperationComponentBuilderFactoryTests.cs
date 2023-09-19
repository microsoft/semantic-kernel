// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Skills.OpenAPI.Builders;
using Xunit;

namespace SemanticKernel.Skills.UnitTests.OpenAPI.Builders;
public class OperationComponentBuilderFactoryTests
{
    [Fact]
    public void ItShouldCreateQueryStringBuilder()
    {
        //Arrange
        var sut = new OperationComponentBuilderFactory();

        //Act
        var builder = sut.CreateQueryStringBuilder();

        //Assert
        Assert.NotNull(builder);
    }
}

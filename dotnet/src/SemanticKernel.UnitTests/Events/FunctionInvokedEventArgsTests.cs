// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Events;
using Xunit;

namespace SemanticKernel.UnitTests.Events;
public class FunctionInvokedEventArgsTests
{
    [Fact]
    public void ResultValuePropertyShouldBeInitializedByOriginalOne()
    {
        //Arrange
        var originalResults = new FunctionResult(new Kernel(), "fake-function-name", 36);

        var sut = new FunctionInvokedEventArgs(KernelFunctionFactory.CreateFromMethod(() => { }), new KernelArguments(), originalResults);

        //Assert
        Assert.Equal(36, sut.ResultValue);
    }

    [Fact]
    public void ResultValuePropertyShouldBeUpdated()
    {
        //Arrange
        var originalResults = new FunctionResult(new Kernel(), "fake-function-name", 36);

        var sut = new FunctionInvokedEventArgs(KernelFunctionFactory.CreateFromMethod(() => { }), new KernelArguments(), originalResults);

        //Act
        sut.SetResultValue(72);

        //Assert
        Assert.Equal(72, sut.ResultValue);
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Linq;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class KernelFunctionMetadataFactoryTests
{
    [Fact]
    public void ItCanCreateFromType()
    {
        // Arrange
        var instanceType = typeof(MyKernelFunctions);

        // Act
        var functionMetadata = KernelFunctionMetadataFactory.CreateFromType(instanceType);

        // Assert
        Assert.NotNull(functionMetadata);
        Assert.Equal(3, functionMetadata.Count<KernelFunctionMetadata>());
        Assert.Contains(functionMetadata, f => f.Name == "Function1");
        Assert.Contains(functionMetadata, f => f.Name == "Function2");
        Assert.Contains(functionMetadata, f => f.Name == "Function3");
    }

    #region private
#pragma warning disable CA1812 // Used in test case above
    private sealed class MyKernelFunctions
    {
        // Disallow instantiation of this class.
        private MyKernelFunctions()
        {
        }

        [KernelFunction("Function1")]
        [Description("Description for function 1.")]
        public string Function1([Description("Description for parameter 1")] string param1) => $"Function1: {param1}";

        [KernelFunction("Function2")]
        [Description("Description for function 2.")]
        public string Function2([Description("Description for parameter 1")] string param1) => $"Function2: {param1}";

        [KernelFunction("Function3")]
        [Description("Description for function 3.")]
        public string Function3([Description("Description for parameter 1")] string param1) => $"Function3: {param1}";
    }
#pragma warning restore CA1812
    #endregion
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel;
using SemanticKernel.UnitTests.Functions.JsonSerializerContexts;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class KernelFunctionMetadataFactoryTests
{
    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public void ItCanCreateFromType(JsonSerializerOptions? jsos)
    {
        // Arrange
        Type type = typeof(MyKernelFunctions);

        // Act
        IEnumerable<KernelFunctionMetadata> metadata = (jsos is not null ?
            KernelFunctionMetadataFactory.CreateFromType(type, jsos) :
            KernelFunctionMetadataFactory.CreateFromType(type)).ToArray();

        // Assert
        Assert.Equal(2, metadata.Count());

        // Assert Function1 metadata
        KernelFunctionMetadata metadata1 = metadata.ElementAt(0);

        Assert.Equal("Function1", metadata1.Name);
        Assert.Equal("Description for function 1.", metadata1.Description);

        Assert.NotEmpty(metadata1.Parameters);
        Assert.NotNull(metadata1.Parameters[0].Schema);
        Assert.Equal("""{"description":"Description for parameter 1","type":"string"}""", metadata1.Parameters[0].Schema!.ToString());

        Assert.NotNull(metadata1.ReturnParameter);
        Assert.NotNull(metadata1.ReturnParameter.Schema);
        Assert.Equal("""{"type":"string"}""", metadata1.ReturnParameter.Schema!.ToString());

        // Assert Function2 metadata
        KernelFunctionMetadata metadata2 = metadata.ElementAt(1);

        Assert.Equal("Function2", metadata2.Name);
        Assert.Equal("Description for function 2.", metadata2.Description);

        Assert.NotEmpty(metadata2.Parameters);
        Assert.NotNull(metadata2.Parameters[0].Schema);
        Assert.Equal("""{"description":"Description for parameter 1","type":"object","properties":{"Value":{"type":["string","null"]}}}""", metadata2.Parameters[0].Schema!.ToString());

        Assert.NotNull(metadata2.ReturnParameter);
        Assert.NotNull(metadata2.ReturnParameter.Schema);
        Assert.Equal("""{"type":"object","properties":{"Result":{"type":"integer"}}}""", metadata2.ReturnParameter.Schema!.ToString());
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public void ItThrowsExceptionIfTypeDoesNotHaveKernelFunctions(JsonSerializerOptions? jsos)
    {
        // Arrange
        Type type = typeof(PluginWithNoKernelFunctions);

        // Act & Assert
        if (jsos is not null)
        {
            Assert.Throws<ArgumentException>(() => KernelFunctionMetadataFactory.CreateFromType(type, jsos));
        }
        else
        {
            Assert.Throws<ArgumentException>(() => KernelFunctionMetadataFactory.CreateFromType(type));
        }
    }

    #region private
#pragma warning disable CA1812 // Used in test case above
    private sealed class MyKernelFunctions
    {
        [KernelFunction("Function1")]
        [Description("Description for function 1.")]
        public string Function1([Description("Description for parameter 1")] string param1) => $"Function1: {param1}";

        [KernelFunction("Function2")]
        [Description("Description for function 2.")]
        private TestReturnType Function3([Description("Description for parameter 1")] TestParameterType param1)
        {
            return new TestReturnType() { Result = int.Parse(param1.Value!) };
        }
    }

    private sealed class PluginWithNoKernelFunctions
    {
        public string Function1([Description("Description for parameter 1")] string param1) => $"Function1: {param1}";

        private TestReturnType Function3([Description("Description for parameter 1")] TestParameterType param1)
        {
            return new TestReturnType() { Result = int.Parse(param1.Value!) };
        }
    }
#pragma warning restore CA1812
    #endregion
}

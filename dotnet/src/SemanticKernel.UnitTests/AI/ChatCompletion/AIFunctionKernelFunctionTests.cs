// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.UnitTests.AI.ChatCompletion;

public class AIFunctionKernelFunctionTests
{
    [Fact]
    public void ShouldAssignIsRequiredParameterMetadataPropertyCorrectly()
    {
        // Arrange and Act
        AIFunction aiFunction = AIFunctionFactory.Create((string p1, int? p2 = null) => p1,
            new AIFunctionFactoryOptions { JsonSchemaCreateOptions = new AIJsonSchemaCreateOptions { RequireAllProperties = false } });

        AIFunctionKernelFunction sut = new(aiFunction);

        // Assert
        KernelParameterMetadata? p1Metadata = sut.Metadata.Parameters.FirstOrDefault(p => p.Name == "p1");
        Assert.True(p1Metadata?.IsRequired);

        KernelParameterMetadata? p2Metadata = sut.Metadata.Parameters.FirstOrDefault(p => p.Name == "p2");
        Assert.False(p2Metadata?.IsRequired);
    }
}

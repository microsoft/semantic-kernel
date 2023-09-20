// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.SkillDefinition;
using Xunit;

namespace SemanticKernel.UnitTests.SkillDefinition;

public class FunctionViewTests
{
    [Fact]
    public void ItReturnsFunctionParams()
    {
        // Arrange
        var paramsA = new List<ParameterView>
        {
            new("p1", "param 1", "default 1"),
            new("p2", "param 2", "default 2")
        };

        // Act
        var funcViewA = new FunctionView("funcA", "s1", "", paramsA, true);

        // Assert
        Assert.NotNull(funcViewA);

        Assert.Equal("p1", funcViewA.Parameters[0].Name);
        Assert.Equal("p2", funcViewA.Parameters[1].Name);
        Assert.Equal("param 1", funcViewA.Parameters[0].Description);
        Assert.Equal("param 2", funcViewA.Parameters[1].Description);
        Assert.Equal("default 1", funcViewA.Parameters[0].DefaultValue);
        Assert.Equal("default 2", funcViewA.Parameters[1].DefaultValue);
    }
}

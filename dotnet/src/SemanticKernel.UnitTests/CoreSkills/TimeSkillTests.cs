// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.CoreSkills;
using Xunit;

namespace SemanticKernel.UnitTests.CoreSkills;

// TODO: allow clock injection and test all functions
public class TimeSkillTests
{
    [Fact]
    public void ItCanBeInstantiated()
    {
        // Act - Assert no exception occurs
        var _ = new TimeSkill();
    }

    [Fact]
    public void ItCanBeImported()
    {
        // Arrange
        var kernel = Kernel.Builder.Build();

        // Act - Assert no exception occurs e.g. due to reflection
        kernel.ImportSkill(new TimeSkill(), "time");
    }
}

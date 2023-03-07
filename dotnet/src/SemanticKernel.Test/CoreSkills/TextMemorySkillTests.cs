// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.CoreSkills;
using Xunit;

namespace SemanticKernelTests.CoreSkills;
public class TextMemorySkillTests
{
    [Fact]
    public void ItCanBeInstantiated()
    {
        var skill = new TextMemorySkill();
    }

    [Fact]
    public void ItCanBeImported()
    {
        // Arange
        var kernel = KernelBuilder.Create();

        // Act
        kernel.ImportSkill(new TextMemorySkill());
    }

    [Fact]
    public void ItCanSaveMemories()
    {

    }

    [Fact]
    public void ItWillOverwriteSavedMemory()
    {

    }

    [Fact]
    public void ItRecallsSingleMemoryByDefault()
    {

    }

    [Fact]
    public void ItCanRecallMultipleMemories()
    {

    }

    [Fact]
    public void ItWillReturnEmptyStringIfNoMemoriesAreRecalled()
    {

    }
}

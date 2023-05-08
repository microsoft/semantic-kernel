// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.CoreSkills;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Xunit;

namespace SemanticKernel.UnitTests.CoreSkills;

public class FileIOSkillTests
{
    private readonly SKContext _context = new(new ContextVariables(), NullMemory.Instance, null, NullLogger.Instance);

    [Fact]
    public void ItCanBeInstantiated()
    {
        // Act - Assert no exception occurs
        _ = new FileIOSkill();
    }

    [Fact]
    public void ItCanBeImported()
    {
        // Arrange
        var kernel = Kernel.Builder.Build();

        // Act - Assert no exception occurs e.g. due to reflection
        _ = kernel.ImportSkill(new FileIOSkill(), "fileIO");
    }

    [Fact]
    public async Task ItCanReadAsync()
    {
        // Arrange
        var skill = new FileIOSkill();
        var path = Path.GetTempFileName();
        File.WriteAllText(path, "hello world");

        // Act
        var result = await skill.ReadAsync(path);

        // Assert
        Assert.Equal("hello world", result);
    }

    [Fact]
    public async Task ItCannotReadAsync()
    {
        // Arrange
        var skill = new FileIOSkill();
        var path = Path.GetTempFileName();
        File.Delete(path);

        // Act
        Task Fn()
        {
            return skill.ReadAsync(path);
        }

        // Assert
        _ = await Assert.ThrowsAsync<FileNotFoundException>(Fn);
    }

    [Fact]
    public async Task ItCanWriteAsync()
    {
        // Arrange
        var skill = new FileIOSkill();
        var path = Path.GetTempFileName();
        this._context["path"] = path;
        this._context["content"] = "hello world";

        // Act
        await skill.WriteAsync(this._context);

        // Assert
        Assert.Equal("hello world", await File.ReadAllTextAsync(path));
    }

    [Fact]
    public async Task ItCannotWriteAsync()
    {
        // Arrange
        var skill = new FileIOSkill();
        var path = Path.GetTempFileName();
        File.SetAttributes(path, FileAttributes.ReadOnly);
        this._context["path"] = path;
        this._context["content"] = "hello world";

        // Act
        Task Fn()
        {
            return skill.WriteAsync(this._context);
        }

        // Assert
        _ = await Assert.ThrowsAsync<UnauthorizedAccessException>(Fn);
    }
}

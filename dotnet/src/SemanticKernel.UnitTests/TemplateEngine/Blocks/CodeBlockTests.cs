// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.TemplateEngine;
using Microsoft.SemanticKernel.TemplateEngine.Blocks;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.TemplateEngine.Blocks;

public class CodeBlockTests
{
    private readonly Mock<IReadOnlySkillCollection> _skills;
    private readonly Mock<ILogger> _log;

    public CodeBlockTests()
    {
        this._skills = new Mock<IReadOnlySkillCollection>();
        this._log = new Mock<ILogger>();
    }

    [Fact]
    public async Task ItThrowsIfAFunctionDoesntExistAsync()
    {
        // Arrange
        var context = new SKContext(new ContextVariables(), NullMemory.Instance, this._skills.Object, this._log.Object);
        this._skills.Setup(x => x.HasNativeFunction("functionName")).Returns(false);
        var target = new CodeBlock("functionName", this._log.Object);

        // Act
        var exception = await Assert.ThrowsAsync<TemplateException>(async () => await target.RenderCodeAsync(context));

        // Assert
        Assert.Equal(TemplateException.ErrorCodes.FunctionNotFound, exception.ErrorCode);
    }

    [Fact]
    public async Task ItThrowsIfAFunctionCallThrowsAsync()
    {
        // Arrange
        var context = new SKContext(new ContextVariables(), NullMemory.Instance, this._skills.Object, this._log.Object);
        var function = new Mock<ISKFunction>();
        function
            .Setup(x => x.InvokeAsync(It.IsAny<SKContext?>(), It.IsAny<CompleteRequestSettings?>(), It.IsAny<ILogger?>(), It.IsAny<CancellationToken?>()))
            .Throws(new RuntimeWrappedException("error"));
        this._skills.Setup(x => x.HasNativeFunction("functionName")).Returns(true);
        this._skills.Setup(x => x.GetNativeFunction("functionName")).Returns(function.Object);
        var target = new CodeBlock("functionName", this._log.Object);

        // Act
        var exception = await Assert.ThrowsAsync<TemplateException>(async () => await target.RenderCodeAsync(context));

        // Assert
        Assert.Equal(TemplateException.ErrorCodes.RuntimeError, exception.ErrorCode);
    }
}

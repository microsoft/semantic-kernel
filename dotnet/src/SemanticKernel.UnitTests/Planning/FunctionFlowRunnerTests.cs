// Copyright (c) Microsoft. All rights reserved.

using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.UnitTests.Planning;

public class FunctionFlowRunnerTests
{
    private readonly ITestOutputHelper _testOutputHelper;

    public FunctionFlowRunnerTests(ITestOutputHelper testOutputHelper)
    {
        this._testOutputHelper = testOutputHelper;
    }

    [Fact]
    public async Task ItExecuteXmlPlanAsyncValidEmptyPlanAsync()
    {
        // Arrange
        var kernelMock = this.CreateKernelMock(out _, out _, out _);
        var kernel = kernelMock.Object;
        var target = new FunctionFlowRunner(kernel);

        var emptyPlanSpec = @"
<goal>Some goal</goal>
<plan>
</plan>
";

        // Act
        var result = await target.ExecuteXmlPlanAsync(this.CreateSKContext(kernel), emptyPlanSpec);

        // Assert
        Assert.NotNull(result);
        Assert.NotNull(result.Variables[SkillPlan.PlanKey]);
    }

    [Theory]
    [InlineData("<goal>Some goal</goal><plan>")]
    public async Task ItExecuteXmlPlanAsyncFailWhenInvalidPlanXmlAsync(string invalidPlanSpec)
    {
        // Arrange
        var kernelMock = this.CreateKernelMock(out _, out _, out _);
        var kernel = kernelMock.Object;
        var target = new FunctionFlowRunner(kernel);

        // Act
        var exception = await Assert.ThrowsAsync<PlanningException>(async () =>
        {
            await target.ExecuteXmlPlanAsync(this.CreateSKContext(kernel), invalidPlanSpec);
        });

        // Assert
        Assert.NotNull(exception);
        Assert.Equal(PlanningException.ErrorCodes.InvalidPlan, exception.ErrorCode);
    }

    [Fact]
    public async Task ItExecuteXmlPlanAsyncAndFailWhenSkillOrFunctionNotExistsAsync()
    {
        // Arrange
        var kernelMock = this.CreateKernelMock(out _, out _, out _);
        var kernel = kernelMock.Object;
        var target = new FunctionFlowRunner(kernel);

        SKContext? result = null;
        // Act
        var exception = await Assert.ThrowsAsync<PlanningException>(async () =>
        {
            result = await target.ExecuteXmlPlanAsync(this.CreateSKContext(kernel), @"
<goal>Some goal</goal>
<plan>
    <function.SkillA.FunctionB/>
</plan>");
        });

        // Assert
        Assert.NotNull(exception);
        Assert.Equal(PlanningException.ErrorCodes.InvalidPlan, exception.ErrorCode);
    }

    [Fact]
    public async Task ItExecuteXmlPlanAsyncFailWhenElseComesWithoutIfAsync()
    {
        // Arrange
        var kernelMock = this.CreateKernelMock(out _, out _, out _);
        var kernel = kernelMock.Object;
        var target = new FunctionFlowRunner(kernel);

        SKContext? result = null;
        // Act
        var exception = await Assert.ThrowsAsync<PlanningException>(async () =>
        {
            result = await target.ExecuteXmlPlanAsync(this.CreateSKContext(kernel), @"
<goal>Some goal</goal>
<plan>
<else>
    <function.SkillA.FunctionB/>
</else>
</plan>");
        });

        // Assert
        Assert.NotNull(exception);
        Assert.Equal(PlanningException.ErrorCodes.InvalidPlan, exception.ErrorCode);
    }

    /// <summary>
    /// Potential tests scenarios with Functions, Ifs and Else (Nested included)
    /// </summary>
    /// <param name="inputPlanSpec">Plan input</param>
    /// <param name="expectedPlanOutput">Expected plan output</param>
    /// <param name="conditionResult">Condition result</param>
    /// <returns>Unit test result</returns>
    private async Task ItExecuteXmlPlanAsyncAndReturnsAsExpectedAsync(string inputPlanSpec, string expectedPlanOutput, bool? conditionResult = null)
    {
        // Arrange
        var kernelMock = this.CreateKernelMock(out _, out var skillMock, out _);
        var kernel = kernelMock.Object;
        var mockFunction = new Mock<ISKFunction>();

        var ifStructureResultContext = this.CreateSKContext(kernel);
        ifStructureResultContext.Variables.Update("{\"valid\": true}");

        var evaluateConditionResultContext = this.CreateSKContext(kernel);
        evaluateConditionResultContext.Variables.Update($"{{\"valid\": true, \"condition\": {((conditionResult ?? false) ? "true" : "false")}}}");

        mockFunction.Setup(f => f.InvokeAsync(It.Is<string>(i => i.StartsWith("<if")),
                It.IsAny<SKContext?>(), It.IsAny<CompleteRequestSettings?>(),
                It.IsAny<ILogger?>(),
                It.IsAny<CancellationToken?>()))
            .ReturnsAsync(ifStructureResultContext);

        mockFunction.Setup(f => f.InvokeAsync(It.Is<string>(i => i.StartsWith("$a equals b")),
                It.IsAny<SKContext?>(), It.IsAny<CompleteRequestSettings?>(),
                It.IsAny<ILogger?>(),
                It.IsAny<CancellationToken?>()))
            .ReturnsAsync(evaluateConditionResultContext);

        skillMock.Setup(s => s.HasSemanticFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(true);
        skillMock.Setup(s => s.GetSemanticFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(mockFunction.Object);
        kernelMock.Setup(k => k.RunAsync(It.IsAny<ContextVariables>(), It.IsAny<ISKFunction>())).ReturnsAsync(this.CreateSKContext(kernel));
        kernelMock.Setup(k => k.RegisterSemanticFunction(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<SemanticFunctionConfig>()))
            .Returns(mockFunction.Object);

        var target = new FunctionFlowRunner(kernel);

        SKContext? result = null;
        // Act
        result = await target.ExecuteXmlPlanAsync(this.CreateSKContext(kernel), inputPlanSpec);

        // Assert
        Assert.NotNull(result);
        Assert.False(result.ErrorOccurred);
        Assert.True(result.Variables.ContainsKey(SkillPlan.PlanKey));
        Assert.Equal(
            NormalizeSpacesBeforeFunctions(expectedPlanOutput),
            NormalizeSpacesBeforeFunctions(result.Variables[SkillPlan.PlanKey]));

        // Removes line breaks and spaces before <function, <if, </if, <else, </else, <while, </while, </plan
        string NormalizeSpacesBeforeFunctions(string input)
        {
            return Regex.Replace(input, @"\s+(?=<function|<[/]*if|<[/]*else|<[/]*while|</plan)", string.Empty, RegexOptions.IgnoreCase)
                .Replace("\n", string.Empty, System.StringComparison.OrdinalIgnoreCase);
        }
    }

    [Theory]
    [InlineData(
        "<goal>Some goal</goal><plan></plan>",
        "<goal>Some goal</goal><plan></plan>")]
    [InlineData(
        "<goal>Some goal</goal><plan><function.SkillA.FunctionB /></plan>",
        "<goal>Some goal</goal><plan></plan>")]
    [InlineData(
        "<goal>Some goal</goal><plan><function.SkillA.FunctionB /><function.SkillA.FunctionC /></plan>",
        "<goal>Some goal</goal><plan>  <function.SkillA.FunctionC /></plan>")]
    public async Task ItExecuteXmlStepPlanAsyncAndReturnsAsExpectedAsync(string inputPlanSpec, string expectedPlanOutput, bool? conditionResult = null)
    {
        await this.ItExecuteXmlPlanAsyncAndReturnsAsExpectedAsync(inputPlanSpec, expectedPlanOutput, conditionResult);
    }

    [Theory]
    [InlineData(
        @"<goal>Some goal</goal>
<plan>
  <function.SkillA.FunctionB />
  <function.SkillA.FunctionC />
  <if condition=""$a equals b"">
    <function.SkillA.FunctionD />
  </if>
</plan>",
        @"<goal>Some goal</goal>
<plan>
  <function.SkillA.FunctionC />
  <if condition=""$a equals b"">
    <function.SkillA.FunctionD />
  </if>
</plan>")]
    [InlineData(
        @"<goal>Some goal</goal>
<plan>
  <if condition=""$a equals b"">
    <function.SkillA.FunctionD />
  </if>
</plan>",
        @"<goal>Some goal</goal>
<plan>
    <function.SkillA.FunctionD />
</plan>", true)]
    [InlineData(
        @"<goal>Some goal</goal>
<plan>
  <if condition=""$a equals b"">
    <function.SkillA.FunctionD />
  </if>
</plan>",
        @"<goal>Some goal</goal>
<plan>
</plan>", false)]
    [InlineData(
        @"<goal>Some goal</goal>
<plan>
  <if condition=""$a equals b"">
    <function.SkillA.FunctionD />
  </if>
  <else>
    <function.SkillX.FunctionW />
  </else>
</plan>",
        @"<goal>Some goal</goal>
<plan>
  <function.SkillX.FunctionW />
</plan>", false)]
    [InlineData(
        @"<goal>Some goal</goal>
<plan>
  <if condition=""$a equals b"">
    <function.SkillA.FunctionD />
  </if>
  <else>
    <function.SkillB.FunctionH />
  </else>
  <if condition=""$b equals c"">
    <function.SkillD.FunctionG />
  </if>
</plan>",
        @"<goal>Some goal</goal>
<plan>
  <function.SkillA.FunctionD />
  <if condition=""$b equals c"">
    <function.SkillD.FunctionG />
  </if>
</plan>", true)]
    [InlineData(
        @"<goal>Some goal</goal>
<plan>
  <if condition=""$a equals b"">
    <function.SkillA.FunctionD />
  </if>
  <else>
    <function.SkillB.FunctionH />
  </else>
  <if condition=""$b equals c"">
    <function.SkillD.FunctionG />
  </if>
</plan>",
        @"<goal>Some goal</goal>
<plan>
  <function.SkillB.FunctionH />
  <if condition=""$b equals c"">
    <function.SkillD.FunctionG />
  </if>
</plan>", false)]
    [InlineData(
        @"<goal>Some goal</goal>
<plan>
  <if condition=""$a equals b"">
    <function.SkillA.FunctionD />
    <if condition=""$b equals c"">
      <function.SkillD.FunctionG />
    </if>
  </if>
  <else>
    <function.SkillB.FunctionH />
  </else>
</plan>",
        @"<goal>Some goal</goal>
<plan>
  <function.SkillA.FunctionD />
  <if condition=""$b equals c"">
    <function.SkillD.FunctionG />
  </if>
</plan>", true)]
    [InlineData(
        @"<goal>Some goal</goal>
<plan>
  <if condition=""$a equals b"">
    <function.SkillA.FunctionD />
    <if condition=""$b equals c"">
      <function.SkillD.FunctionG />
    </if>
  </if>
  <else>
    <function.SkillB.FunctionH />
  </else>
</plan>",
        @"<goal>Some goal</goal>
<plan>
  <function.SkillB.FunctionH />
</plan>", false)]
    public async Task ItExecuteXmlIfPlanAsyncAndReturnsAsExpectedAsync(string inputPlanSpec, string expectedPlanOutput, bool? conditionResult = null)
    {
        await this.ItExecuteXmlPlanAsyncAndReturnsAsExpectedAsync(inputPlanSpec, expectedPlanOutput, conditionResult);
    }

    [Theory]
    [InlineData(
        @"<goal>Some goal</goal>
<plan>
  <function.SkillA.FunctionB />
  <function.SkillA.FunctionC />
  <while condition=""$a equals b"">
    <function.SkillA.FunctionD />
  </while>
</plan>",
        @"<goal>Some goal</goal>
<plan>
  <function.SkillA.FunctionC />
  <while condition=""$a equals b"">
    <function.SkillA.FunctionD />
  </while>
</plan>")]
    [InlineData(
        @"<goal>Some goal</goal>
<plan>
  <while condition=""$a equals b"">
    <function.SkillA.FunctionD />
  </while>
</plan>",
        @"<goal>Some goal</goal>
<plan>
  <function.SkillA.FunctionD />
  <while condition=""$a equals b"">
    <function.SkillA.FunctionD />
  </while>
</plan>", true)]
    [InlineData(
        @"<goal>Some goal</goal>
<plan>
  <while condition=""$a equals b"">
    <function.SkillA.FunctionD />
  </while>
</plan>",
        @"<goal>Some goal</goal>
<plan>
</plan>", false)]
    [InlineData(
        @"<goal>Some goal</goal>
<plan>
  <while condition=""$a equals b"">
    <function.SkillA.FunctionD />
  </while>
  <function.SkillX.FunctionW />
</plan>",
        @"<goal>Some goal</goal>
<plan>
  <function.SkillX.FunctionW />
</plan>", false)]
    [InlineData(
        @"<goal>Some goal</goal>
<plan>
  <while condition=""$a equals b"">
    <function.SkillA.FunctionD />
  </while>
  <function.SkillB.FunctionH />
  <if condition=""$b equals c"">
    <function.SkillD.FunctionG />
  </if>
</plan>",
        @"<goal>Some goal</goal>
<plan>
  <function.SkillA.FunctionD />
  <while condition=""$a equals b"">
    <function.SkillA.FunctionD />
  </while>
  <function.SkillB.FunctionH />
  <if condition=""$b equals c"">
    <function.SkillD.FunctionG />
  </if>
</plan>", true)]
    [InlineData(
        @"<goal>Some goal</goal>
<plan>
  <while condition=""$a equals b"">
    <function.SkillA.FunctionD />
  </while>
  <function.SkillB.FunctionH />
  <if condition=""$b equals c"">
    <function.SkillD.FunctionG />
  </if>
</plan>",
        @"<goal>Some goal</goal>
<plan>
  <function.SkillB.FunctionH />
  <if condition=""$b equals c"">
    <function.SkillD.FunctionG />
  </if>
</plan>", false)]
    [InlineData(
        @"<goal>Some goal</goal>
<plan>
  <while condition=""$a equals b"">
    <function.SkillA.FunctionD />
    <if condition=""$b equals c"">
      <function.SkillD.FunctionG />
    </if>
  </while>
</plan>",
        @"<goal>Some goal</goal>
<plan>
  <function.SkillA.FunctionD />
  <if condition=""$b equals c"">
    <function.SkillD.FunctionG />
  </if>
  <while condition=""$a equals b"">
    <function.SkillA.FunctionD />
    <if condition=""$b equals c"">
      <function.SkillD.FunctionG />
    </if>
  </while>
</plan>", true)]
    [InlineData(
        @"<goal>Some goal</goal>
<plan>
  <while condition=""$a equals b"">
    <function.SkillA.FunctionD />
    <if condition=""$b equals c"">
      <function.SkillD.FunctionG />
    </if>
  </while>
  <function.SkillB.FunctionH />
</plan>",
        @"<goal>Some goal</goal>
<plan>
  <function.SkillB.FunctionH />
</plan>", false)]
    public async Task ItExecuteXmlWhilePlanAsyncAndReturnsAsExpectedAsync(string inputPlanSpec, string expectedPlanOutput, bool? conditionResult = null)
    {
        await this.ItExecuteXmlPlanAsyncAndReturnsAsExpectedAsync(inputPlanSpec, expectedPlanOutput, conditionResult);
    }

    private SKContext CreateSKContext(
        IKernel kernel,
        ContextVariables? variables = null,
        CancellationToken cancellationToken = default)
    {
        return new SKContext(variables ?? new ContextVariables(), kernel.Memory, kernel.Skills, kernel.Log, cancellationToken);
    }

    private Mock<IKernel> CreateKernelMock(
        out Mock<ISemanticTextMemory> semanticMemoryMock,
        out Mock<IReadOnlySkillCollection> mockSkillCollection,
        out Mock<ILogger> mockLogger)
    {
        semanticMemoryMock = new Mock<ISemanticTextMemory>();
        mockSkillCollection = new Mock<IReadOnlySkillCollection>();
        mockLogger = new Mock<ILogger>();

        var kernelMock = new Mock<IKernel>();
        kernelMock.SetupGet(k => k.Skills).Returns(mockSkillCollection.Object);
        kernelMock.SetupGet(k => k.Log).Returns(mockLogger.Object);
        kernelMock.SetupGet(k => k.Memory).Returns(semanticMemoryMock.Object);

        return kernelMock;
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows;
using Microsoft.SemanticKernel.Process.Workflows.PowerFx;
using Xunit;
using Xunit.Abstractions;

namespace Microsoft.SemanticKernel.Process.UnitTests.Workflows.PowerFx;

public class TemplateExtensionsTests(ITestOutputHelper output) : RecalcEngineTest(output)
{
    [Fact]
    public void FormatTemplateLines()
    {
        // Arrange
        List<TemplateLine> template =
        [
            TemplateLine.Parse("Hello"),
            TemplateLine.Parse(" "),
            TemplateLine.Parse("World"),
        ];
        RecalcEngine engine = this.CreateEngine();

        // Act
        string? result = engine.Format(template);

        // Assert
        Assert.Equal("Hello World", result);
    }

    [Fact]
    public void FormatTemplateLinesEmpty()
    {
        // Arrange
        List<TemplateLine> template = [];
        RecalcEngine engine = this.CreateEngine();

        // Act
        string? result = engine.Format(template);

        // Assert
        Assert.Equal(string.Empty, result);
    }

    [Fact]
    public void FormatTemplateLine()
    {
        // Arrange
        TemplateLine line = TemplateLine.Parse("Test");
        RecalcEngine engine = this.CreateEngine();

        // Act
        string? result = engine.Format(line);

        // Assert
        Assert.Equal("Test", result);
    }

    [Fact]
    public void FormatTemplateLineNull()
    {
        // Arrange
        TemplateLine? line = null;
        RecalcEngine engine = this.CreateEngine();

        // Act
        string? result = engine.Format(line);

        // Assert
        Assert.Equal(string.Empty, result);
    }

    [Fact]
    public void FormatTextSegment()
    {
        // Arrange
        TemplateSegment textSegment = TextSegment.FromText("Hello World");
        TemplateLine line = new([textSegment]);
        RecalcEngine engine = this.CreateEngine();

        // Act
        string? result = engine.Format(line);

        // Assert
        Assert.Equal("Hello World", result);
    }

    [Fact]
    public void FormatExpressionSegment()
    {
        // Arrange
        ExpressionSegment expressionSegment = new(ValueExpression.Expression("1 + 1"));
        TemplateLine line = new([expressionSegment]);
        RecalcEngine engine = this.CreateEngine();

        // Act
        string? result = engine.Format(line);

        // Assert
        Assert.Equal("2", result);
    }

    [Fact]
    public void FormatVariableSegment()
    {
        // Arrange
        this.Scopes.Set("Source", FormulaValue.New("Hello World"));
        ExpressionSegment expressionSegment = new(ValueExpression.Variable(PropertyPath.TopicVariable("Source")));
        TemplateLine line = new([expressionSegment]);
        RecalcEngine engine = this.CreateEngine();

        // Act
        string? result = engine.Format(line);

        // Assert
        Assert.Equal("Hello World", result);
    }

    //[Fact]
    //public void Format_WithExpressionSegmentWithVariableReference_ReturnsEvaluatedValue()
    //{
    //    // Arrange
    //    Mock<VariableReference> mockVariableRef = new();
    //    mockVariableRef.Setup(vr => vr.ToString()).Returns("myVariable");

    //    Expression expression = new() { VariableReference = mockVariableRef.Object };
    //    ExpressionSegment expressionSegment = new() { Expression = expression };
    //    TemplateLine line = new([expressionSegment]);

    //    _mockFormulaValue.Setup(fv => fv.Format()).Returns("VariableValue");
    //    _mockEngine.Setup(e => e.Eval("myVariable")).Returns(_mockFormulaValue.Object);

    //    // Act
    //    string? result = engine.Format(line);

    //    // Assert
    //    Assert.Equal("VariableValue", result);
    //    _mockEngine.Verify(e => e.Eval("myVariable"), Times.Once);
    //    _mockFormulaValue.Verify(fv => fv.Format(), Times.Once);
    //}

    [Fact]
    public void FormatExpressionSegmentUndefined()
    {
        // Arrange
        ExpressionSegment expressionSegment = new();
        TemplateLine line = new([expressionSegment]);
        RecalcEngine engine = this.CreateEngine();

        // Act & Assert
        Assert.Throws<InvalidSegmentException>(() => engine.Format(line));
    }

    [Fact]
    public void FormatMultipleSegments()
    {
        // Arrange
        TemplateSegment textSegment = TextSegment.FromText("Hello ");
        ExpressionSegment expressionSegment = new(ValueExpression.Expression(@"""World"""));
        TemplateLine line = new([textSegment, expressionSegment]);
        RecalcEngine engine = this.CreateEngine();

        // Act
        string? result = engine.Format(line);

        // Assert
        Assert.Equal("Hello World", result);
    }
}

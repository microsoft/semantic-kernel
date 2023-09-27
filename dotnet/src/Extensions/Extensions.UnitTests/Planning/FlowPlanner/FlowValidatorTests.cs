// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Extensions.UnitTests.Planning.FlowPlanner;

using System;
using Microsoft.SemanticKernel.Planning.Flow;
using Xunit;

public class FlowValidatorTests
{
    [Fact]
    public void TestValidateFlowReturnsTrueForValidFlow()
    {
        // Arrange
        var validator = new FlowValidator();
        var flow = new Flow("test_flow", "test flow goal");
        var step1 = new FlowStep("step1");
        step1.AddProvides("a");
        var step2 = new FlowStep("step2");
        step2.AddRequires("a");
        step2.AddProvides("b");
        var step3 = new FlowStep("step3");
        step3.AddRequires("a", "b");
        step3.AddProvides("c");
        var step4 = new ReferenceFlowStep("another flow")
        {
            CompletionType = CompletionType.Optional,
            StartingMessage = "Would you like to start another flow?"
        };
        flow.AddStep(step1);
        flow.AddStep(step2);
        flow.AddStep(step3);
        flow.AddStep(step4);

        // Act and assert
        validator.Validate(flow);
    }

    [Fact]
    public void TestValidateFlowThrowForEmptyFlow()
    {
        // Arrange
        var validator = new FlowValidator();
        var flow = new Flow("empty flow", "empty flow");

        // Act and assert
        Assert.Throws<ArgumentException>(() => validator.Validate(flow));
    }

    [Fact]
    public void TestValidateFlowThrowForFlowWithDependencyLoops()
    {
        // Arrange
        var validator = new FlowValidator();
        var flow = new Flow("test_flow", "test flow goal");
        var step1 = new FlowStep("step1");
        step1.AddRequires("a");
        step1.AddProvides("b");
        var step2 = new FlowStep("step2");
        step2.AddRequires("b");
        step2.AddProvides("a");
        flow.AddStep(step1);
        flow.AddStep(step2);

        // Act and assert
        Assert.Throws<ArgumentException>(() => validator.Validate(flow));
    }

    [Fact]
    public void TestValidateFlowThrowForReferenceStepWithRequires()
    {
        // Arrange
        var validator = new FlowValidator();
        var flow = new Flow("test_flow", "test flow goal");
        var step1 = new ReferenceFlowStep("another flow");
        step1.AddRequires("a");

        // Act and assert
        Assert.Throws<ArgumentException>(() => validator.Validate(flow));
    }

    [Fact]
    public void TestValidateFlowThrowForReferenceStepWithProvides()
    {
        // Arrange
        var validator = new FlowValidator();
        var flow = new Flow("test_flow", "test flow goal");
        var step1 = new ReferenceFlowStep("another flow");
        step1.AddProvides("a");

        // Act and assert
        Assert.Throws<ArgumentException>(() => validator.Validate(flow));
    }

    [Fact]
    public void TestValidateFlowThrowForOptionalStepWithoutStartingMessage()
    {
        // Arrange
        var validator = new FlowValidator();
        var flow = new Flow("test_flow", "test flow goal");
        var step1 = new FlowStep("step1");
        step1.AddProvides("a");
        var step2 = new ReferenceFlowStep("another flow")
        {
            CompletionType = CompletionType.Optional
        };
        flow.AddStep(step1);
        flow.AddStep(step2);

        // Act and assert
        Assert.Throws<ArgumentException>(() => validator.Validate(flow));
    }
}

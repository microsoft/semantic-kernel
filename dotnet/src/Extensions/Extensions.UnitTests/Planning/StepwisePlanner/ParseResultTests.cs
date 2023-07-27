// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;

namespace SemanticKernel.Extensions.UnitTests.Planning.StepwisePlanner;

public sealed class ParseResultTests
{
    [Theory]
    [InlineData("[FINAL ANSWER] 42", "42")]
    [InlineData("[FINAL ANSWER]42", "42")]
    [InlineData("I think I have everything I need.\n[FINAL ANSWER] 42", "42")]
    [InlineData("I think I have everything I need.\n[FINAL ANSWER] 42\n", "42")]
    [InlineData("I think I have everything I need.\n[FINAL ANSWER] 42\n\n", "42")]
    [InlineData("I think I have everything I need.\n[FINAL ANSWER]42\n\n\n", "42")]
    [InlineData("I think I have everything I need.\n[FINAL ANSWER]\n 42\n\n\n", "42")]
    public void WhenInputIsFinalAnswerReturnsFinalAnswer(string input, string expected)
    {
        // Arrange
        var kernel = new Mock<IKernel>();
        kernel.Setup(x => x.Logger).Returns(new Mock<ILogger>().Object);

        var planner = new Microsoft.SemanticKernel.Planning.StepwisePlanner(kernel.Object);

        // Act
        var result = planner.ParseResult(input);

        // Assert
        Assert.Equal(expected, result.FinalAnswer);
    }

    [Theory]
    [InlineData("To answer the first part of the question, I need to search for Leo DiCaprio's girlfriend on the web. To answer the second part, I need to find her current age and use a calculator to raise it to the 0.43 power.\n[ACTION]\n{\n  \"action\": \"Search\",\n  \"action_variables\": {\"input\": \"Leo DiCaprio's girlfriend\"}\n}", "Search", "input", "Leo DiCaprio's girlfriend")]
    [InlineData("To answer the first part of the question, I need to search the web for Leo DiCaprio's girlfriend. To answer the second part, I need to find her current age and use the calculator tool to raise it to the 0.43 power.\n[ACTION]\n```\n{\n  \"action\": \"Search\",\n  \"action_variables\": {\"input\": \"Leo DiCaprio's girlfriend\"}\n}\n```", "Search", "input", "Leo DiCaprio's girlfriend")]
    [InlineData("The web search result is a snippet from a Wikipedia article that says Leo DiCaprio's girlfriend is Camila Morrone, an Argentine-American model and actress. I need to find out her current age, which might be in the same article or another source. I can use the WebSearch.Search function again to search for her name and age.\n\n[ACTION] {\n  \"action\": \"WebSearch.Search\",\n \"action_variables\": {\"input\": \"Camila Morrone age\", \"count\": \"1\"}\n}", "WebSearch.Search", "input",
        "Camila Morrone age", "count", "1")]
    public void ParseActionReturnsAction(string input, string expectedAction, params string[] expectedVariables)
    {
        Dictionary<string, string>? expectedDictionary = null;
        for (int i = 0; i < expectedVariables.Length; i += 2)
        {
            expectedDictionary ??= new Dictionary<string, string>();
            expectedDictionary.Add(expectedVariables[i], expectedVariables[i + 1]);
        }

        // Arrange
        var kernel = new Mock<IKernel>();
        kernel.Setup(x => x.Logger).Returns(new Mock<ILogger>().Object);

        var planner = new Microsoft.SemanticKernel.Planning.StepwisePlanner(kernel.Object);

        // Act
        var result = planner.ParseResult(input);

        // Assert
        Assert.Equal(expectedAction, result.Action);
        Assert.Equal(expectedDictionary, result.ActionVariables);
    }

    // Method to create Mock<ISKFunction> objects
    private static Mock<ISKFunction> CreateMockFunction(FunctionView functionView)
    {
        var mockFunction = new Mock<ISKFunction>();
        mockFunction.Setup(x => x.Describe()).Returns(functionView);
        mockFunction.Setup(x => x.Name).Returns(functionView.Name);
        mockFunction.Setup(x => x.SkillName).Returns(functionView.SkillName);
        return mockFunction;
    }
}

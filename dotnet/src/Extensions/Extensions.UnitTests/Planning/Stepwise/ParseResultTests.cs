// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning.StepwisePlanner;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;

namespace SemanticKernel.Extensions.UnitTests.Planning.Stepwise;

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
    [InlineData("I think I have everything I need.\n\n[FINALANSWER]\n 42\n\n\n", "42")]
    [InlineData("I think I have everything I need.\n[FINAL_ANSWER]\n 42\n\n\n", "42")]
    [InlineData("I think I have everything I need.\n[FINAL-ANSWER]\n 42\n\n\n", "42")]
    public void WhenInputIsFinalAnswerReturnsFinalAnswer(string input, string expected)
    {
        // Arrange
        var kernel = new Mock<IKernel>();
        kernel.Setup(x => x.LoggerFactory).Returns(new Mock<ILoggerFactory>().Object);

        var planner = new Microsoft.SemanticKernel.Planning.StepwisePlanner(kernel.Object);

        // Act
        var result = planner.ParseResult(input);

        // Assert
        Assert.Equal(expected, result.FinalAnswer);
    }

    [Theory]
    [InlineData("To answer the first part of the question, I need to search.\n[ACTION]\n{\n  \"action\": \"Search\",\n  \"action_variables\": {\"input\": \"something to search\"}\n}", "To answer the first part of the question, I need to search.", "Search", "input", "something to search")]
    [InlineData("To answer the first part of the question, I need to search.\n[ACTION]\n```\n{\n  \"action\": \"Search\",\n  \"action_variables\": {\"input\": \"something to search\"}\n}\n```", "To answer the first part of the question, I need to search.", "Search", "input", "something to search")]
    [InlineData("The web search result is a snippet from a Wikipedia article that says something.\n\n[ACTION] {\n  \"action\": \"WebSearch.Search\",\n \"action_variables\": {\"input\": \"another search\", \"count\": \"1\"}\n}", "The web search result is a snippet from a Wikipedia article that says something.", "WebSearch.Search", "input",
        "another search", "count", "1")]
    [InlineData("[ACTION] {\"action\": \"time.Year\", \"action_variables\": {\"input\": \"\"}}", null, "time.Year", "input", "")]
    [InlineData(@"[ACTION]{
  ""action"": ""RepositorySkill.PushChangesToBranch"",
  ""action_variables"": {
    ""branchName"": ""myBranchName"",
    ""comment"": ""{MyComment""
  }
}
", null, "RepositorySkill.PushChangesToBranch", "branchName", "myBranchName", "comment", "{MyComment")]
    [InlineData(@"[ACTION]{
  ""action"": ""RepositorySkill.PushChangesToBranch"",
  ""action_variables"": {
    ""branchName"": ""myBranchName"",
    ""comment"": ""}MyComment""
  }
}
", null, "RepositorySkill.PushChangesToBranch", "branchName", "myBranchName", "comment", "}MyComment")]
    [InlineData(@"[ACTION]{
  ""action"": ""RepositorySkill.PushChangesToBranch"",
  ""action_variables"": {
    ""branchName"": ""myBranchName"",
    ""comment"": ""{MyComment}""
  }
}
", null, "RepositorySkill.PushChangesToBranch", "branchName", "myBranchName", "comment", "{MyComment}")]
    public void ParseActionReturnsAction(string input, string expectedThought, string expectedAction, params string[] expectedVariables)
    {
        Dictionary<string, string>? expectedDictionary = null;
        for (int i = 0; i < expectedVariables.Length; i += 2)
        {
            expectedDictionary ??= new Dictionary<string, string>();
            expectedDictionary.Add(expectedVariables[i], expectedVariables[i + 1]);
        }

        // Arrange
        var kernel = new Mock<IKernel>();
        kernel.Setup(x => x.LoggerFactory).Returns(new Mock<ILoggerFactory>().Object);

        var planner = new Microsoft.SemanticKernel.Planning.StepwisePlanner(kernel.Object);

        // Act
        var result = planner.ParseResult(input);

        // Assert
        Assert.Equal(expectedAction ?? string.Empty, result.Action);
        Assert.Equal(expectedDictionary, result.ActionVariables);
        Assert.Equal(expectedThought ?? string.Empty, result.Thought);
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

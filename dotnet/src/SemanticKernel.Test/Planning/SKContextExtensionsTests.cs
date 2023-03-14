// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using SemanticKernelTests.XunitHelpers;
using Xunit;
using static Microsoft.SemanticKernel.CoreSkills.PlannerSkill;

namespace SemanticKernelTests.Planning;

public class SKContextExtensionsTests
{
    [Fact]
    public async Task CanCallGetAvailableFunctionsWithNoFunctionsAsync()
    {
        // mock the SKContext components
        var variables = new ContextVariables();
        var memory = new Mock<ISemanticTextMemory>();
        var skills = new SkillCollection();
        var logger = ConsoleLogger.Log;
        var cancellationToken = default(CancellationToken);

        var memoryQueryResult = new MemoryQueryResult(false, "sourceName", "id", "description", "text", 0.8);
        var asyncEnumerable = new[] { memoryQueryResult }.ToAsyncEnumerable();
        memory.Setup(x => x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<CancellationToken>()))
            .Returns(asyncEnumerable);

        var context = new SKContext(variables, memory.Object, skills.ReadOnlySkillCollection, logger, cancellationToken);
        var config = new PlannerSkillConfig();
        var semanticQuery = "test";
        var result = await context.GetAvailableFunctionsAsync(config, semanticQuery).ConfigureAwait(true);
        Assert.NotNull(result);
    }

    [Fact]
    public async Task CanCallGetAvailableFunctionsWithFunctionsAsync()
    {
        var variables = new ContextVariables();
        var memory = new Mock<ISemanticTextMemory>();
        var skills = new Mock<ISkillCollection>();
        var logger = ConsoleLogger.Log;
        var cancellationToken = default(CancellationToken);
        var mockSemanticFunction = new Mock<ISKFunction>();
        var mockNativeFunction = new Mock<ISKFunction>();

        var functionsView = new FunctionsView();
        var functionView = new FunctionView("functionName", "skillName", "description", new List<ParameterView>(), true, false);
        var nativeFunctionView = new FunctionView("nativeFunctionName", "skillName", "description", new List<ParameterView>(), false, false);
        functionsView.AddFunction(functionView);
        functionsView.AddFunction(nativeFunctionView);

        var memoryQueryResult = new MemoryQueryResult(false, "sourceName", functionView.ToFullyQualifiedName(), "description", "text", 0.8);
        var asyncEnumerable = new[] { memoryQueryResult }.ToAsyncEnumerable();
        memory.Setup(x => x.SearchAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<int>(), It.IsAny<double>(), It.IsAny<CancellationToken>()))
            .Returns(asyncEnumerable);

        skills.Setup(x => x.HasFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(true);
        skills.Setup(x => x.HasSemanticFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(true);
        skills.Setup(x => x.HasNativeFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(true);
        skills.Setup(x => x.GetSemanticFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(mockSemanticFunction.Object);
        skills.Setup(x => x.GetNativeFunction(It.IsAny<string>(), It.IsAny<string>())).Returns(mockNativeFunction.Object);
        skills.Setup(x => x.GetFunctionsView(It.IsAny<bool>(), It.IsAny<bool>())).Returns(functionsView);
        skills.SetupGet(x => x.ReadOnlySkillCollection).Returns(skills.Object);

        var context = new SKContext(variables, memory.Object, skills.Object, logger, cancellationToken);
        var config = new PlannerSkillConfig();
        var semanticQuery = "test";
        var result = await context.GetAvailableFunctionsAsync(config, semanticQuery).ConfigureAwait(true);
        Assert.NotNull(result);
        // Verify result is just 1 match
        // Verify the function is the one we expect
        Assert.Single(result);
        Assert.Equal(functionView, result[0]);

        config.IncludedFunctions.UnionWith(new List<string> { "nativeFunctionName" });
        result = await context.GetAvailableFunctionsAsync(config, semanticQuery).ConfigureAwait(true);
        Assert.NotNull(result);
        Assert.Equal(2, result.Count);
        Assert.Equal(functionView, result[0]);
        Assert.Equal(nativeFunctionView, result[1]);
    }
}

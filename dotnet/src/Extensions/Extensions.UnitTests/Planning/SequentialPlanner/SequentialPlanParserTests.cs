// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning.Sequential;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Extensions.UnitTests.Planning.SequentialPlanner;

public class SequentialPlanParserTests
{
    private readonly ITestOutputHelper _testOutputHelper;

    public SequentialPlanParserTests(ITestOutputHelper testOutputHelper)
    {
        this._testOutputHelper = testOutputHelper;
    }

    private Mock<IKernel> CreateKernelMock(
        out Mock<IReadOnlySkillCollection> mockSkillCollection,
        out Mock<ILogger> mockLogger)
    {
        mockSkillCollection = new Mock<IReadOnlySkillCollection>();
        mockLogger = new Mock<ILogger>();

        var kernelMock = new Mock<IKernel>();
        kernelMock.SetupGet(k => k.Skills).Returns(mockSkillCollection.Object);
        kernelMock.SetupGet(k => k.LoggerFactory).Returns(new Mock<ILoggerFactory>().Object);

        return kernelMock;
    }

    private SKContext CreateSKContext(
        IKernel kernel,
        ContextVariables? variables = null)
    {
        return new SKContext(variables, kernel.Skills, kernel.LoggerFactory);
    }

    private static Mock<ISKFunction> CreateMockFunction(FunctionView functionView, string result = "")
    {
        var mockFunction = new Mock<ISKFunction>();
        mockFunction.Setup(x => x.Describe()).Returns(functionView);
        mockFunction.Setup(x => x.Name).Returns(functionView.Name);
        mockFunction.Setup(x => x.SkillName).Returns(functionView.SkillName);
        return mockFunction;
    }

    private void CreateKernelAndFunctionCreateMocks(List<(string name, string skillName, string description, bool isSemantic, string result)> functions,
        out IKernel kernel)
    {
        var kernelMock = this.CreateKernelMock(out var skills, out _);
        kernel = kernelMock.Object;

        // For Create
        kernelMock.Setup(k => k.CreateNewContext()).Returns(this.CreateSKContext(kernel));

        var functionsView = new FunctionsView();
        foreach (var (name, skillName, description, isSemantic, resultString) in functions)
        {
            var functionView = new FunctionView(name, skillName, description, new List<ParameterView>() { new(name: "param", description: "description") }, isSemantic, true);
            var mockFunction = CreateMockFunction(functionView);
            functionsView.AddFunction(functionView);

            var result = this.CreateSKContext(kernel);
            result.Variables.Update(resultString);
            mockFunction.Setup(x => x.InvokeAsync(It.IsAny<SKContext>(), null, It.IsAny<CancellationToken>()))
                .ReturnsAsync(result);

            if (string.IsNullOrEmpty(name))
            {
                kernelMock.Setup(x => x.RegisterSemanticFunction(
                    It.IsAny<string>(),
                    It.IsAny<string>(),
                    It.IsAny<SemanticFunctionConfig>()
                )).Returns(mockFunction.Object);
            }
            else
            {
                skills.Setup(x => x.GetFunction(It.Is<string>(s => s == skillName), It.Is<string>(s => s == name)))
                    .Returns(mockFunction.Object);
                ISKFunction? outFunc = mockFunction.Object;
                skills.Setup(x => x.TryGetFunction(It.Is<string>(s => s == name), out outFunc)).Returns(true);
                skills.Setup(x => x.TryGetFunction(It.Is<string>(s => s == skillName), It.Is<string>(s => s == name), out outFunc)).Returns(true);
            }
        }

        skills.Setup(x => x.GetFunctionsView(It.IsAny<bool>(), It.IsAny<bool>())).Returns(functionsView);
    }

    [Fact]
    public void CanCallToPlanFromXml()
    {
        // Arrange
        var functions = new List<(string name, string skillName, string description, bool isSemantic, string result)>()
        {
            ("Summarize", "SummarizeSkill", "Summarize an input", true, "This is the summary."),
            ("Translate", "WriterSkill", "Translate to french", true, "Bonjour!"),
            ("GetEmailAddressAsync", "email", "Get email address", false, "johndoe@email.com"),
            ("SendEmailAsync", "email", "Send email", false, "Email sent."),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        var planString =
            @"
<plan>
    <function.SummarizeSkill.Summarize/>
    <function.WriterSkill.Translate language=""French"" setContextVariable=""TRANSLATED_SUMMARY""/>
    <function.email.GetEmailAddressAsync input=""John Doe"" setContextVariable=""EMAIL_ADDRESS"" appendToResult=""PLAN_RESULT""/>
    <function.email.SendEmailAsync input=""$TRANSLATED_SUMMARY"" email_address=""$EMAIL_ADDRESS""/>
</plan>";
        var goal = "Summarize an input, translate to french, and e-mail to John Doe";

        // Act
        var plan = planString.ToPlanFromXml(goal, SequentialPlanParser.GetSkillFunction(kernel.Skills));

        // Assert
        Assert.NotNull(plan);
        Assert.Equal("Summarize an input, translate to french, and e-mail to John Doe", plan.Description);

        Assert.Equal(4, plan.Steps.Count);
        Assert.Collection(plan.Steps,
            step =>
            {
                Assert.Equal("SummarizeSkill", step.SkillName);
                Assert.Equal("Summarize", step.Name);
            },
            step =>
            {
                Assert.Equal("WriterSkill", step.SkillName);
                Assert.Equal("Translate", step.Name);
                Assert.Equal("French", step.Parameters["language"]);
                Assert.True(step.Outputs.Contains("TRANSLATED_SUMMARY"));
            },
            step =>
            {
                Assert.Equal("email", step.SkillName);
                Assert.Equal("GetEmailAddressAsync", step.Name);
                Assert.Equal("John Doe", step.Parameters["input"]);
                Assert.True(step.Outputs.Contains("EMAIL_ADDRESS"));
            },
            step =>
            {
                Assert.Equal("email", step.SkillName);
                Assert.Equal("SendEmailAsync", step.Name);
                Assert.Equal("$TRANSLATED_SUMMARY", step.Parameters["input"]);
                Assert.Equal("$EMAIL_ADDRESS", step.Parameters["email_address"]);
            }
        );
    }

    private const string GoalText = "Solve the equation x^2 = 2.";

    [Fact]
    public void InvalidPlanExecutePlanReturnsInvalidResult()
    {
        // Arrange
        this.CreateKernelAndFunctionCreateMocks(new(), out var kernel);
        var planString = "<someTag>";

        // Act
        Assert.Throws<SKException>(() => planString.ToPlanFromXml(GoalText, SequentialPlanParser.GetSkillFunction(kernel.Skills)));
    }

    // Test that contains a #text node in the plan
    [Theory]
    [InlineData("Test the functionFlowRunner", @"<goal>Test the functionFlowRunner</goal>
    <plan>
    <function.MockSkill.Echo input=""Hello World"" />
    This is some text
    </plan>")]
    public void CanCreatePlanWithTextNodes(string goalText, string planText)
    {
        // Arrange
        var functions = new List<(string name, string skillName, string description, bool isSemantic, string result)>()
        {
            ("Echo", "MockSkill", "Echo an input", true, "Mock Echo Result"),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        // Act
        var plan = planText.ToPlanFromXml(goalText, SequentialPlanParser.GetSkillFunction(kernel.Skills));

        // Assert
        Assert.NotNull(plan);
        Assert.Equal(goalText, plan.Description);
        Assert.Equal(1, plan.Steps.Count);
        Assert.Equal("MockSkill", plan.Steps[0].SkillName);
        Assert.Equal("Echo", plan.Steps[0].Name);
    }

    [Theory]
    [InlineData("Test the functionFlowRunner", @"<goal>Test the functionFlowRunner</goal>
    <plan>
    <function.MockSkill.Echo input=""Hello World"" />")]
    public void CanCreatePlanWithPartialXml(string goalText, string planText)
    {
        // Arrange
        var functions = new List<(string name, string skillName, string description, bool isSemantic, string result)>()
        {
            ("Echo", "MockSkill", "Echo an input", true, "Mock Echo Result"),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        // Act
        var plan = planText.ToPlanFromXml(goalText, SequentialPlanParser.GetSkillFunction(kernel.Skills));

        // Assert
        Assert.NotNull(plan);
        Assert.Equal(goalText, plan.Description);
        Assert.Equal(1, plan.Steps.Count);
        Assert.Equal("MockSkill", plan.Steps[0].SkillName);
        Assert.Equal("Echo", plan.Steps[0].Name);
    }

    [Theory]
    [InlineData("Test the functionFlowRunner", @"<goal>Test the functionFlowRunner</goal>
    <plan>
    <function.Echo input=""Hello World"" />
    </plan>")]
    public void CanCreatePlanWithFunctionName(string goalText, string planText)
    {
        // Arrange
        var functions = new List<(string name, string skillName, string description, bool isSemantic, string result)>()
        {
            ("Echo", "_GLOBAL_FUNCTIONS_", "Echo an input", true, "Mock Echo Result"),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        // Act
        var plan = planText.ToPlanFromXml(goalText, SequentialPlanParser.GetSkillFunction(kernel.Skills));

        // Assert
        Assert.NotNull(plan);
        Assert.Equal(goalText, plan.Description);
        Assert.Equal(1, plan.Steps.Count);
        Assert.Equal("_GLOBAL_FUNCTIONS_", plan.Steps[0].SkillName);
        Assert.Equal("Echo", plan.Steps[0].Name);
    }

    // Test that contains a #text node in the plan
    [Theory]
    [InlineData(@"
    <plan>
    <function.MockSkill.Echo input=""Hello World"" />
    <function.MockSkill.DoesNotExist input=""Hello World"" />
    </plan>", true)]
    [InlineData(@"
    <plan>
    <function.MockSkill.Echo input=""Hello World"" />
    <function.MockSkill.DoesNotExist input=""Hello World"" />
    </plan>", false)]
    public void CanCreatePlanWithInvalidFunctionNodes(string planText, bool allowMissingFunctions)
    {
        // Arrange
        var functions = new List<(string name, string skillName, string description, bool isSemantic, string result)>()
        {
            ("Echo", "MockSkill", "Echo an input", true, "Mock Echo Result"),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        // Act
        if (allowMissingFunctions)
        {
            // it should not throw
            var plan = planText.ToPlanFromXml(string.Empty, SequentialPlanParser.GetSkillFunction(kernel.Skills), allowMissingFunctions);

            // Assert
            Assert.NotNull(plan);
            Assert.Equal(2, plan.Steps.Count);

            Assert.Equal("MockSkill", plan.Steps[0].SkillName);
            Assert.Equal("Echo", plan.Steps[0].Name);
            Assert.Null(plan.Steps[0].Description);

            Assert.Equal(plan.GetType().Name, plan.Steps[1].SkillName);
            Assert.NotEmpty(plan.Steps[1].Name);
            Assert.Equal("MockSkill.DoesNotExist", plan.Steps[1].Description);
        }
        else
        {
            Assert.Throws<SKException>(() => planText.ToPlanFromXml(string.Empty, SequentialPlanParser.GetSkillFunction(kernel.Skills), allowMissingFunctions));
        }
    }

    [Theory]
    [InlineData("Test the functionFlowRunner", @"Possible result: <goal>Test the functionFlowRunner</goal>
    <plan>
    <function.MockSkill.Echo input=""Hello World"" />
    This is some text
    </plan>")]
    [InlineData("Test the functionFlowRunner", @"
    <plan>
    <function.MockSkill.Echo input=""Hello World"" />
    This is some text
    </plan>

    plan end")]
    [InlineData("Test the functionFlowRunner", @"
    <plan>
    <function.MockSkill.Echo input=""Hello World"" />
    This is some text
    </plan>

    plan <xml> end")]
    public void CanCreatePlanWithOtherText(string goalText, string planText)
    {
        // Arrange
        var functions = new List<(string name, string skillName, string description, bool isSemantic, string result)>()
        {
            ("Echo", "MockSkill", "Echo an input", true, "Mock Echo Result"),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        // Act
        var plan = planText.ToPlanFromXml(goalText, SequentialPlanParser.GetSkillFunction(kernel.Skills));

        // Assert
        Assert.NotNull(plan);
        Assert.Equal(goalText, plan.Description);
        Assert.Equal(1, plan.Steps.Count);
        Assert.Equal("MockSkill", plan.Steps[0].SkillName);
        Assert.Equal("Echo", plan.Steps[0].Name);
    }

    [Theory]
    [InlineData(@"<plan> <function.CodeSearch.codesearchresults_post organization=""MyOrg"" project=""Proj"" api_version=""7.1-preview.1"" server_url=""https://faketestorg.dev.azure.com/"" payload=""{&quot;searchText&quot;:&quot;test&quot;,&quot;$top&quot;:3,&quot;filters&quot;:{&quot;Repository/Project&quot;:[&quot;Proj&quot;],&quot;Repository/Repository&quot;:[&quot;Repo&quot;]}}"" content_type=""application/json"" appendToResult=""RESULT__TOP_THREE_RESULTS"" /> </plan>")]
    [InlineData("<plan>\n  <function.CodeSearch.codesearchresults_post organization=\"MyOrg\" project=\"MyProject\" api_version=\"7.1-preview.1\" payload=\"{&quot;searchText&quot;: &quot;MySearchText&quot;, &quot;filters&quot;: {&quot;pathFilters&quot;: [&quot;MyRepo&quot;]} }\" setContextVariable=\"SEARCH_RESULTS\"/>\n</plan><!-- END -->")]
    [InlineData("<plan>\n  <function.CodeSearch.codesearchresults_post organization=\"MyOrg\" project=\"MyProject\" api_version=\"7.1-preview.1\" server_url=\"https://faketestorg.dev.azure.com/\" payload=\"{ 'searchText': 'MySearchText', 'filters': { 'Project': ['MyProject'], 'Repository': ['MyRepo'] }, 'top': 3, 'skip': 0 }\" content_type=\"application/json\" appendToResult=\"RESULT__TOP_THREE_RESULTS\" />\n</plan><!-- END -->")]
    public void CanCreatePlanWithOpenApiPlugin(string planText)
    {
        // Arrange
        var functions = new List<(string name, string skillName, string description, bool isSemantic, string result)>()
        {
            ("codesearchresults_post", "CodeSearch", "Echo an input", true, "Mock Echo Result"),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        // Act
        var plan = planText.ToPlanFromXml(string.Empty, SequentialPlanParser.GetSkillFunction(kernel.Skills));

        // Assert
        Assert.NotNull(plan);
        Assert.Equal(1, plan.Steps.Count);
        Assert.Equal("CodeSearch", plan.Steps[0].SkillName);
        Assert.Equal("codesearchresults_post", plan.Steps[0].Name);
    }

    // test that a <tag> that is not <function> will just get skipped
    [Theory]
    [InlineData("Test the functionFlowRunner", @"<plan>
    <function.MockSkill.Echo input=""Hello World"" />
    <tag>Some other tag</tag>
    <function.MockSkill.Echo />
    </plan>")]
    public void CanCreatePlanWithIgnoredNodes(string goalText, string planText)
    {
        // Arrange
        var functions = new List<(string name, string skillName, string description, bool isSemantic, string result)>()
        {
            ("Echo", "MockSkill", "Echo an input", true, "Mock Echo Result"),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        // Act
        var plan = planText.ToPlanFromXml(goalText, SequentialPlanParser.GetSkillFunction(kernel.Skills));

        // Assert
        Assert.NotNull(plan);
        Assert.Equal(goalText, plan.Description);
        Assert.Equal(2, plan.Steps.Count);
        Assert.Equal("MockSkill", plan.Steps[0].SkillName);
        Assert.Equal("Echo", plan.Steps[0].Name);
        Assert.Equal(0, plan.Steps[1].Steps.Count);
        Assert.Equal("MockSkill", plan.Steps[1].SkillName);
        Assert.Equal("Echo", plan.Steps[1].Name);
    }
}

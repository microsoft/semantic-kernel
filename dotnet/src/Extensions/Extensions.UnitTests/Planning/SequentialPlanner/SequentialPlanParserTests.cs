// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning.Sequential;
using Microsoft.SemanticKernel.SemanticFunctions;
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
        out Mock<IReadOnlyFunctionCollection> mockFunctionCollection,
        out Mock<ILogger> mockLogger)
    {
        mockFunctionCollection = new Mock<IReadOnlyFunctionCollection>();
        mockLogger = new Mock<ILogger>();

        var kernelMock = new Mock<IKernel>();
        kernelMock.SetupGet(k => k.Functions).Returns(mockFunctionCollection.Object);
        kernelMock.SetupGet(k => k.LoggerFactory).Returns(new Mock<ILoggerFactory>().Object);

        return kernelMock;
    }

    private SKContext CreateSKContext(
        IKernelExecutionContext kernelContext,
        ContextVariables? variables = null)
    {
        return new SKContext(kernelContext, variables);
    }

    private static Mock<ISKFunction> CreateMockFunction(FunctionView functionView, string result = "")
    {
        var mockFunction = new Mock<ISKFunction>();
        mockFunction.Setup(x => x.Describe()).Returns(functionView);
        mockFunction.Setup(x => x.Name).Returns(functionView.Name);
        mockFunction.Setup(x => x.PluginName).Returns(functionView.PluginName);
        return mockFunction;
    }

    private void CreateKernelAndFunctionCreateMocks(List<(string name, string pluginName, string description, bool isSemantic, string result)> functions,
        out IKernel kernel)
    {
        var kernelMock = this.CreateKernelMock(out var functionCollection, out _);
        kernel = kernelMock.Object;

        var kernelContextMock = new Mock<IKernelExecutionContext>();

        // For Create
        kernelMock.Setup(k => k.CreateNewContext(It.IsAny<ContextVariables>(), It.IsAny<IReadOnlyFunctionCollection>()))
            .Returns<ContextVariables, IReadOnlyFunctionCollection>((contextVariables, skills) =>
            {
                kernelContextMock.SetupGet(x => x.Functions).Returns(skills ?? kernelMock.Object.Functions);
                return this.CreateSKContext(kernelContextMock.Object, contextVariables);
            });

        var functionsView = new List<FunctionView>();
        foreach (var (name, pluginName, description, isSemantic, resultString) in functions)
        {
            var functionView = new FunctionView(name, pluginName, description)
            {
                Parameters = new ParameterView[] { new("param", "description") }
            };
            var mockFunction = CreateMockFunction(functionView);
            functionsView.Add(functionView);

            var result = this.CreateSKContext(kernelContextMock.Object);
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
                functionCollection.Setup(x => x.GetFunction(It.Is<string>(s => s == pluginName), It.Is<string>(s => s == name)))
                    .Returns(mockFunction.Object);
                ISKFunction? outFunc = mockFunction.Object;
                functionCollection.Setup(x => x.TryGetFunction(It.Is<string>(s => s == name), out outFunc)).Returns(true);
                functionCollection.Setup(x => x.TryGetFunction(It.Is<string>(s => s == pluginName), It.Is<string>(s => s == name), out outFunc)).Returns(true);
            }
        }

        functionCollection.Setup(x => x.GetFunctionViews()).Returns(functionsView);

        kernelContextMock.SetupGet(x => x.Functions).Returns(functionCollection.Object);
    }

    [Fact]
    public void CanCallToPlanFromXml()
    {
        // Arrange
        var functions = new List<(string name, string pluginName, string description, bool isSemantic, string result)>()
        {
            ("Summarize", "SummarizePlugin", "Summarize an input", true, "This is the summary."),
            ("Translate", "WriterPlugin", "Translate to french", true, "Bonjour!"),
            ("GetEmailAddressAsync", "email", "Get email address", false, "johndoe@email.com"),
            ("SendEmailAsync", "email", "Send email", false, "Email sent."),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        var planString =
            @"
<plan>
    <function.SummarizePlugin.Summarize/>
    <function.WriterPlugin.Translate language=""French"" setContextVariable=""TRANSLATED_SUMMARY""/>
    <function.email.GetEmailAddressAsync input=""John Doe"" setContextVariable=""EMAIL_ADDRESS"" appendToResult=""PLAN_RESULT""/>
    <function.email.SendEmailAsync input=""$TRANSLATED_SUMMARY"" email_address=""$EMAIL_ADDRESS""/>
</plan>";
        var goal = "Summarize an input, translate to french, and e-mail to John Doe";

        // Act
        var plan = planString.ToPlanFromXml(goal, SequentialPlanParser.GetPluginFunction(kernel.Functions));

        // Assert
        Assert.NotNull(plan);
        Assert.Equal("Summarize an input, translate to french, and e-mail to John Doe", plan.Description);

        Assert.Equal(4, plan.Steps.Count);
        Assert.Collection(plan.Steps,
            step =>
            {
                Assert.Equal("SummarizePlugin", step.PluginName);
                Assert.Equal("Summarize", step.Name);
            },
            step =>
            {
                Assert.Equal("WriterPlugin", step.PluginName);
                Assert.Equal("Translate", step.Name);
                Assert.Equal("French", step.Parameters["language"]);
                Assert.True(step.Outputs.Contains("TRANSLATED_SUMMARY"));
            },
            step =>
            {
                Assert.Equal("email", step.PluginName);
                Assert.Equal("GetEmailAddressAsync", step.Name);
                Assert.Equal("John Doe", step.Parameters["input"]);
                Assert.True(step.Outputs.Contains("EMAIL_ADDRESS"));
            },
            step =>
            {
                Assert.Equal("email", step.PluginName);
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
        Assert.Throws<SKException>(() => planString.ToPlanFromXml(GoalText, SequentialPlanParser.GetPluginFunction(kernel.Functions)));
    }

    // Test that contains a #text node in the plan
    [Theory]
    [InlineData("Test the functionFlowRunner", @"<goal>Test the functionFlowRunner</goal>
    <plan>
    <function.MockPlugin.Echo input=""Hello World"" />
    This is some text
    </plan>")]
    public void CanCreatePlanWithTextNodes(string goalText, string planText)
    {
        // Arrange
        var functions = new List<(string name, string pluginName, string description, bool isSemantic, string result)>()
        {
            ("Echo", "MockPlugin", "Echo an input", true, "Mock Echo Result"),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        // Act
        var plan = planText.ToPlanFromXml(goalText, SequentialPlanParser.GetPluginFunction(kernel.Functions));

        // Assert
        Assert.NotNull(plan);
        Assert.Equal(goalText, plan.Description);
        Assert.Single(plan.Steps);
        Assert.Equal("MockPlugin", plan.Steps[0].PluginName);
        Assert.Equal("Echo", plan.Steps[0].Name);
    }

    [Theory]
    [InlineData("Test the functionFlowRunner", @"<goal>Test the functionFlowRunner</goal>
    <plan>
    <function.MockPlugin.Echo input=""Hello World"" />")]
    public void CanCreatePlanWithPartialXml(string goalText, string planText)
    {
        // Arrange
        var functions = new List<(string name, string pluginName, string description, bool isSemantic, string result)>()
        {
            ("Echo", "MockPlugin", "Echo an input", true, "Mock Echo Result"),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        // Act
        var plan = planText.ToPlanFromXml(goalText, SequentialPlanParser.GetPluginFunction(kernel.Functions));

        // Assert
        Assert.NotNull(plan);
        Assert.Equal(goalText, plan.Description);
        Assert.Single(plan.Steps);
        Assert.Equal("MockPlugin", plan.Steps[0].PluginName);
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
        var functions = new List<(string name, string pluginName, string description, bool isSemantic, string result)>()
        {
            ("Echo", "_GLOBAL_FUNCTIONS_", "Echo an input", true, "Mock Echo Result"),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        // Act
        var plan = planText.ToPlanFromXml(goalText, SequentialPlanParser.GetPluginFunction(kernel.Functions));

        // Assert
        Assert.NotNull(plan);
        Assert.Equal(goalText, plan.Description);
        Assert.Single(plan.Steps);
        Assert.Equal("_GLOBAL_FUNCTIONS_", plan.Steps[0].PluginName);
        Assert.Equal("Echo", plan.Steps[0].Name);
    }

    // Test that contains a #text node in the plan
    [Theory]
    [InlineData(@"
    <plan>
    <function.MockPlugin.Echo input=""Hello World"" />
    <function.MockPlugin.DoesNotExist input=""Hello World"" />
    </plan>", true)]
    [InlineData(@"
    <plan>
    <function.MockPlugin.Echo input=""Hello World"" />
    <function.MockPlugin.DoesNotExist input=""Hello World"" />
    </plan>", false)]
    public void CanCreatePlanWithInvalidFunctionNodes(string planText, bool allowMissingFunctions)
    {
        // Arrange
        var functions = new List<(string name, string pluginName, string description, bool isSemantic, string result)>()
        {
            ("Echo", "MockPlugin", "Echo an input", true, "Mock Echo Result"),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        // Act
        if (allowMissingFunctions)
        {
            // it should not throw
            var plan = planText.ToPlanFromXml(string.Empty, SequentialPlanParser.GetPluginFunction(kernel.Functions), allowMissingFunctions);

            // Assert
            Assert.NotNull(plan);
            Assert.Equal(2, plan.Steps.Count);

            Assert.Equal("MockPlugin", plan.Steps[0].PluginName);
            Assert.Equal("Echo", plan.Steps[0].Name);
            Assert.Null(plan.Steps[0].Description);

            Assert.Equal(plan.GetType().Name, plan.Steps[1].PluginName);
            Assert.NotEmpty(plan.Steps[1].Name);
            Assert.Equal("MockPlugin.DoesNotExist", plan.Steps[1].Description);
        }
        else
        {
            Assert.Throws<SKException>(() => planText.ToPlanFromXml(string.Empty, SequentialPlanParser.GetPluginFunction(kernel.Functions), allowMissingFunctions));
        }
    }

    [Theory]
    [InlineData("Test the functionFlowRunner", @"Possible result: <goal>Test the functionFlowRunner</goal>
    <plan>
    <function.MockPlugin.Echo input=""Hello World"" />
    This is some text
    </plan>")]
    [InlineData("Test the functionFlowRunner", @"
    <plan>
    <function.MockPlugin.Echo input=""Hello World"" />
    This is some text
    </plan>

    plan end")]
    [InlineData("Test the functionFlowRunner", @"
    <plan>
    <function.MockPlugin.Echo input=""Hello World"" />
    This is some text
    </plan>

    plan <xml> end")]
    public void CanCreatePlanWithOtherText(string goalText, string planText)
    {
        // Arrange
        var functions = new List<(string name, string pluginName, string description, bool isSemantic, string result)>()
        {
            ("Echo", "MockPlugin", "Echo an input", true, "Mock Echo Result"),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        // Act
        var plan = planText.ToPlanFromXml(goalText, SequentialPlanParser.GetPluginFunction(kernel.Functions));

        // Assert
        Assert.NotNull(plan);
        Assert.Equal(goalText, plan.Description);
        Assert.Single(plan.Steps);
        Assert.Equal("MockPlugin", plan.Steps[0].PluginName);
        Assert.Equal("Echo", plan.Steps[0].Name);
    }

    [Theory]
    [InlineData(@"<plan> <function.CodeSearch.codesearchresults_post organization=""MyOrg"" project=""Proj"" api_version=""7.1-preview.1"" server_url=""https://faketestorg.dev.azure.com/"" payload=""{&quot;searchText&quot;:&quot;test&quot;,&quot;$top&quot;:3,&quot;filters&quot;:{&quot;Repository/Project&quot;:[&quot;Proj&quot;],&quot;Repository/Repository&quot;:[&quot;Repo&quot;]}}"" content_type=""application/json"" appendToResult=""RESULT__TOP_THREE_RESULTS"" /> </plan>")]
    [InlineData("<plan>\n  <function.CodeSearch.codesearchresults_post organization=\"MyOrg\" project=\"MyProject\" api_version=\"7.1-preview.1\" payload=\"{&quot;searchText&quot;: &quot;MySearchText&quot;, &quot;filters&quot;: {&quot;pathFilters&quot;: [&quot;MyRepo&quot;]} }\" setContextVariable=\"SEARCH_RESULTS\"/>\n</plan><!-- END -->")]
    [InlineData("<plan>\n  <function.CodeSearch.codesearchresults_post organization=\"MyOrg\" project=\"MyProject\" api_version=\"7.1-preview.1\" server_url=\"https://faketestorg.dev.azure.com/\" payload=\"{ 'searchText': 'MySearchText', 'filters': { 'Project': ['MyProject'], 'Repository': ['MyRepo'] }, 'top': 3, 'skip': 0 }\" content_type=\"application/json\" appendToResult=\"RESULT__TOP_THREE_RESULTS\" />\n</plan><!-- END -->")]
    public void CanCreatePlanWithOpenApiPlugin(string planText)
    {
        // Arrange
        var functions = new List<(string name, string pluginName, string description, bool isSemantic, string result)>()
        {
            ("codesearchresults_post", "CodeSearch", "Echo an input", true, "Mock Echo Result"),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        // Act
        var plan = planText.ToPlanFromXml(string.Empty, SequentialPlanParser.GetPluginFunction(kernel.Functions));

        // Assert
        Assert.NotNull(plan);
        Assert.Single(plan.Steps);
        Assert.Equal("CodeSearch", plan.Steps[0].PluginName);
        Assert.Equal("codesearchresults_post", plan.Steps[0].Name);
    }

    // test that a <tag> that is not <function> will just get skipped
    [Theory]
    [InlineData("Test the functionFlowRunner", @"<plan>
    <function.MockPlugin.Echo input=""Hello World"" />
    <tag>Some other tag</tag>
    <function.MockPlugin.Echo />
    </plan>")]
    public void CanCreatePlanWithIgnoredNodes(string goalText, string planText)
    {
        // Arrange
        var functions = new List<(string name, string pluginName, string description, bool isSemantic, string result)>()
        {
            ("Echo", "MockPlugin", "Echo an input", true, "Mock Echo Result"),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        // Act
        var plan = planText.ToPlanFromXml(goalText, SequentialPlanParser.GetPluginFunction(kernel.Functions));

        // Assert
        Assert.NotNull(plan);
        Assert.Equal(goalText, plan.Description);
        Assert.Equal(2, plan.Steps.Count);
        Assert.Equal("MockPlugin", plan.Steps[0].PluginName);
        Assert.Equal("Echo", plan.Steps[0].Name);
        Assert.Empty(plan.Steps[1].Steps);
        Assert.Equal("MockPlugin", plan.Steps[1].PluginName);
        Assert.Equal("Echo", plan.Steps[1].Name);
    }
}

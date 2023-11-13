// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Services;
using Moq;
using Xunit;
using Xunit.Abstractions;

#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel.Planners.Sequential.UnitTests;
#pragma warning restore IDE0130 // Namespace does not match folder structure

public class SequentialPlanParserTests
{
    private readonly ITestOutputHelper _testOutputHelper;

    public SequentialPlanParserTests(ITestOutputHelper testOutputHelper)
    {
        this._testOutputHelper = testOutputHelper;
    }

    private Mock<IKernel> CreateKernelMock(
        out Mock<ILogger> mockLogger)
    {
        mockLogger = new Mock<ILogger>();

        var kernelMock = new Mock<IKernel>();
        kernelMock.SetupGet(k => k.Plugins).Returns(new SKPluginCollection());
        kernelMock.SetupGet(k => k.LoggerFactory).Returns(NullLoggerFactory.Instance);

        return kernelMock;
    }

    private SKContext CreateSKContext(
        IFunctionRunner functionRunner,
        IAIServiceProvider serviceProvider,
        IAIServiceSelector serviceSelector,
        ContextVariables? variables = null)
    {
        return new SKContext(functionRunner, serviceProvider, serviceSelector, variables);
    }

    private void CreateKernelAndFunctionCreateMocks(List<(string name, string pluginName, string description, string result)> functions,
        out IKernel kernel)
    {
        var kernelMock = this.CreateKernelMock(out var functionCollection);
        kernel = kernelMock.Object;

        var functionRunnerMock = new Mock<IFunctionRunner>();
        var serviceProviderMock = new Mock<IAIServiceProvider>();
        var serviceSelector = new Mock<IAIServiceSelector>();

        // For Create
        kernelMock.Setup(k => k.CreateNewContext(It.IsAny<ContextVariables>(), It.IsAny<IReadOnlySKPluginCollection>(), It.IsAny<ILoggerFactory>(), It.IsAny<CultureInfo>()))
            .Returns<ContextVariables, IReadOnlySKPluginCollection, ILoggerFactory, CultureInfo>((contextVariables, skills, loggerFactory, culture) =>
            {
                return this.CreateSKContext(functionRunnerMock.Object, serviceProviderMock.Object, serviceSelector.Object, contextVariables);
            });

        SKPluginCollection plugins = new();
        foreach (var pluginFunctions in functions.GroupBy(f => f.pluginName, StringComparer.OrdinalIgnoreCase))
        {
            plugins.Add(new SKPlugin(
                pluginFunctions.Key,
                from f in pluginFunctions select KernelFunctionFromMethod.Create(() => f.result, f.name, f.description)));
        }
        kernelMock.Setup(k => k.Plugins).Returns(plugins);
    }

    [Fact]
    public void CanCallToPlanFromXml()
    {
        // Arrange
        var functions = new List<(string name, string pluginName, string description, string result)>()
        {
            ("Summarize", "SummarizePlugin", "Summarize an input", "This is the summary."),
            ("Translate", "WriterPlugin", "Translate to french", "Bonjour!"),
            ("GetEmailAddressAsync", "email", "Get email address", "johndoe@email.com"),
            ("SendEmailAsync", "email", "Send email", "Email sent."),
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
        var plan = planString.ToPlanFromXml(goal, kernel.Plugins.GetFunctionCallback());

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
        Assert.Throws<SKException>(() => planString.ToPlanFromXml(GoalText, kernel.Plugins.GetFunctionCallback()));
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
        var functions = new List<(string name, string pluginName, string description, string result)>()
        {
            ("Echo", "MockPlugin", "Echo an input", "Mock Echo Result"),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        // Act
        var plan = planText.ToPlanFromXml(goalText, kernel.Plugins.GetFunctionCallback());

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
        var functions = new List<(string name, string pluginName, string description, string result)>()
        {
            ("Echo", "MockPlugin", "Echo an input", "Mock Echo Result"),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        // Act
        var plan = planText.ToPlanFromXml(goalText, kernel.Plugins.GetFunctionCallback());

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
    <function.Global.Echo input=""Hello World"" />
    </plan>")]
    public void CanCreatePlanWithFunctionName(string goalText, string planText)
    {
        // Arrange
        var functions = new List<(string name, string pluginName, string description, string result)>()
        {
            ("Echo", "Global", "Echo an input", "Mock Echo Result"),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        // Act
        var plan = planText.ToPlanFromXml(goalText, kernel.Plugins.GetFunctionCallback());

        // Assert
        Assert.NotNull(plan);
        Assert.Equal(goalText, plan.Description);
        Assert.Single(plan.Steps);
        Assert.Equal("Global", plan.Steps[0].PluginName);
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
        var functions = new List<(string name, string pluginName, string description, string result)>()
        {
            ("Echo", "MockPlugin", "Echo an input", "Mock Echo Result"),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        // Act
        if (allowMissingFunctions)
        {
            // it should not throw
            var plan = planText.ToPlanFromXml(string.Empty, kernel.Plugins.GetFunctionCallback(), allowMissingFunctions);

            // Assert
            Assert.NotNull(plan);
            Assert.Equal(2, plan.Steps.Count);

            Assert.Equal("MockPlugin", plan.Steps[0].PluginName);
            Assert.Equal("Echo", plan.Steps[0].Name);
            Assert.Equal("Echo an input", plan.Steps[0].Description);

            Assert.Equal("MockPlugin", plan.Steps[1].PluginName);
            Assert.NotEmpty(plan.Steps[1].Name);
            Assert.Equal("MockPlugin.DoesNotExist", plan.Steps[1].Description);
        }
        else
        {
            Assert.Throws<SKException>(() => planText.ToPlanFromXml(string.Empty, kernel.Plugins.GetFunctionCallback(), allowMissingFunctions));
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
        var functions = new List<(string name, string pluginName, string description, string result)>()
        {
            ("Echo", "MockPlugin", "Echo an input", "Mock Echo Result"),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        // Act
        var plan = planText.ToPlanFromXml(goalText, kernel.Plugins.GetFunctionCallback());

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
        var functions = new List<(string name, string pluginName, string description, string result)>()
        {
            ("codesearchresults_post", "CodeSearch", "Echo an input", "Mock Echo Result"),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        // Act
        var plan = planText.ToPlanFromXml(string.Empty, kernel.Plugins.GetFunctionCallback());

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
        var functions = new List<(string name, string pluginName, string description, string result)>()
        {
            ("Echo", "MockPlugin", "Echo an input", "Mock Echo Result"),
        };
        this.CreateKernelAndFunctionCreateMocks(functions, out var kernel);

        // Act
        var plan = planText.ToPlanFromXml(goalText, kernel.Plugins.GetFunctionCallback());

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

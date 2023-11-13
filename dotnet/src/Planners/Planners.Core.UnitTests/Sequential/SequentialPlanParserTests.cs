// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
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

    [Fact]
    public void CanCallToPlanFromXml()
    {
        // Arrange
        var functions = new List<(string name, string pluginName, string description, bool isSemantic)>()
        {
            ("Summarize", "SummarizePlugin", "Summarize an input", true),
            ("Translate", "WriterPlugin", "Translate to french", true),
            ("GetEmailAddressAsync", "email", "Get email address", false),
            ("SendEmailAsync", "email", "Send email", false),
        };

        var functionCollection = this.CreateFunctionCollection(functions);

        var planString =
            @"<plan>
                    <function.SummarizePlugin.Summarize/>
                    <function.WriterPlugin.Translate language=""French"" setContextVariable=""TRANSLATED_SUMMARY""/>
                    <function.email.GetEmailAddressAsync input=""John Doe"" setContextVariable=""EMAIL_ADDRESS"" appendToResult=""PLAN_RESULT""/>
                    <function.email.SendEmailAsync input=""$TRANSLATED_SUMMARY"" email_address=""$EMAIL_ADDRESS""/>
              </plan>";

        var kernel = this.CreateKernel(planString, functionCollection);

        var goal = "Summarize an input, translate to french, and e-mail to John Doe";

        // Act
        var plan = planString.ToPlanFromXml(goal, kernel.Functions.GetFunctionCallback());

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

    [Fact]
    public void InvalidPlanExecutePlanReturnsInvalidResult()
    {
        // Arrange
        var planString = "<someTag>";

        var kernel = this.CreateKernel(planString);

        // Act
        Assert.Throws<SKException>(() => planString.ToPlanFromXml("Solve the equation x^2 = 2.", kernel.Functions.GetFunctionCallback()));
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
        var functions = new List<(string name, string pluginName, string description, bool isSemantic)>()
        {
            ("Echo", "MockPlugin", "Echo an input", true),
        };

        var functionCollection = this.CreateFunctionCollection(functions);

        var kernel = this.CreateKernel(planText, functionCollection);

        // Act
        var plan = planText.ToPlanFromXml(goalText, kernel.Functions.GetFunctionCallback());

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
        var functions = new List<(string name, string pluginName, string description, bool isSemantic)>()
        {
            ("Echo", "MockPlugin", "Echo an input", true),
        };

        var functionCollection = this.CreateFunctionCollection(functions);

        var kernel = this.CreateKernel(planText, functionCollection);

        // Act
        var plan = planText.ToPlanFromXml(goalText, kernel.Functions.GetFunctionCallback());

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
        var functions = new List<(string name, string pluginName, string description, bool isSemantic)>()
        {
            ("Echo", FunctionCollection.GlobalFunctionsPluginName, "Echo an input", true),
        };

        var functionCollection = this.CreateFunctionCollection(functions);

        var kernel = this.CreateKernel(planText, functionCollection);

        // Act
        var plan = planText.ToPlanFromXml(goalText, kernel.Functions.GetFunctionCallback());

        // Assert
        Assert.NotNull(plan);
        Assert.Equal(goalText, plan.Description);
        Assert.Single(plan.Steps);
        Assert.Equal(FunctionCollection.GlobalFunctionsPluginName, plan.Steps[0].PluginName);
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
        var functions = new List<(string name, string pluginName, string description, bool isSemantic)>()
        {
            ("Echo", "MockPlugin", "Echo an input", true),
        };

        var functionCollection = this.CreateFunctionCollection(functions);

        var kernel = this.CreateKernel(planText, functionCollection);

        // Act
        if (allowMissingFunctions)
        {
            // it should not throw
            var plan = planText.ToPlanFromXml(string.Empty, kernel.Functions.GetFunctionCallback(), allowMissingFunctions);

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
            Assert.Throws<SKException>(() => planText.ToPlanFromXml(string.Empty, kernel.Functions.GetFunctionCallback(), allowMissingFunctions));
        }
    }

    [Theory]
    [InlineData("Test the functionFlowRunner",
        @"Possible result: <goal>Test the functionFlowRunner</goal>
        <plan>
            <function.MockPlugin.Echo input=""Hello World"" />
            This is some text
        </plan>")]
    [InlineData("Test the functionFlowRunner",
        @"<plan>
            <function.MockPlugin.Echo input=""Hello World"" />
            This is some text
          </plan>
          plan end")]
    [InlineData("Test the functionFlowRunner",
        @"<plan>
            <function.MockPlugin.Echo input=""Hello World"" />
            This is some text
          </plan>
          plan <xml> end")]
    public void CanCreatePlanWithOtherText(string goalText, string planText)
    {
        // Arrange
        var functions = new List<(string name, string pluginName, string description, bool isSemantic)>()
        {
            ("Echo", "MockPlugin", "Echo an input", true),
        };

        var functionCollection = this.CreateFunctionCollection(functions);

        var kernel = this.CreateKernel(planText, functionCollection);

        // Act
        var plan = planText.ToPlanFromXml(goalText, kernel.Functions.GetFunctionCallback());

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
        var functions = new List<(string name, string pluginName, string description, bool isSemantic)>()
        {
            ("codesearchresults_post", "CodeSearch", "Echo an input", true),
        };

        var functionCollection = this.CreateFunctionCollection(functions);

        var kernel = this.CreateKernel(planText, functionCollection);

        // Act
        var plan = planText.ToPlanFromXml(string.Empty, kernel.Functions.GetFunctionCallback());

        // Assert
        Assert.NotNull(plan);
        Assert.Single(plan.Steps);
        Assert.Equal("CodeSearch", plan.Steps[0].PluginName);
        Assert.Equal("codesearchresults_post", plan.Steps[0].Name);
    }

    // test that a <tag> that is not <function> will just get skipped
    [Theory]
    [InlineData("Test the functionFlowRunner",
        @"<plan>
            <function.MockPlugin.Echo input=""Hello World"" />
            <tag>Some other tag</tag>
            <function.MockPlugin.Echo />
          </plan>")]
    public void CanCreatePlanWithIgnoredNodes(string goalText, string planText)
    {
        // Arrange
        var functions = new List<(string name, string pluginName, string description, bool isSemantic)>()
        {
            ("Echo", "MockPlugin", "Echo an input", true),
        };

        var functionCollection = this.CreateFunctionCollection(functions);

        var kernel = this.CreateKernel(planText, functionCollection);

        // Act
        var plan = planText.ToPlanFromXml(goalText, kernel.Functions.GetFunctionCallback());

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

    private Kernel CreateKernel(string testPlanString, FunctionCollection? functions = null)
    {
        if (functions is null)
        {
            functions = new FunctionCollection();
        }

        var textResult = new Mock<ITextResult>();
        textResult
            .Setup(tr => tr.GetCompletionAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(testPlanString);

        var textCompletionResult = new List<ITextResult> { textResult.Object };

        var textCompletion = new Mock<ITextCompletion>();
        textCompletion
            .Setup(tc => tc.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<AIRequestSettings>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(textCompletionResult);

        var serviceSelector = new Mock<IAIServiceSelector>();
        serviceSelector
            .Setup(ss => ss.SelectAIService<ITextCompletion>(It.IsAny<SKContext>(), It.IsAny<ISKFunction>()))
            .Returns((textCompletion.Object, new AIRequestSettings()));

        var functionRunner = new Mock<IFunctionRunner>();
        var serviceProvider = new Mock<IAIServiceProvider>();

        return new Kernel(serviceProvider.Object, functions, serviceSelector.Object);
    }

    private FunctionCollection CreateFunctionCollection(List<(string name, string pluginName, string description, bool isSemantic)> functions)
    {
        var collection = new FunctionCollection();

        foreach (var (name, pluginName, description, isSemantic) in functions)
        {
            var functionView = new FunctionView(name, pluginName, description);
            var mockFunction = CreateMockFunction(functionView);

            mockFunction.Setup(x => x.InvokeAsync(
                It.IsAny<SKContext>(),
                It.IsAny<AIRequestSettings?>(),
                It.IsAny<CancellationToken>()))
                .Returns<
                    SKContext,
                    AIRequestSettings,
                    CancellationToken>((context, settings, CancellationToken) =>
                    {
                        return Task.FromResult(new FunctionResult(name, pluginName, context));
                    });

            collection.AddFunction(mockFunction.Object);
        }

        return collection;
    }

    // Method to create Mock<ISKFunction> objects
    private static Mock<ISKFunction> CreateMockFunction(FunctionView functionView)
    {
        var mockFunction = new Mock<ISKFunction>();
        mockFunction.Setup(x => x.Describe()).Returns(functionView);
        mockFunction.Setup(x => x.Name).Returns(functionView.Name);
        mockFunction.Setup(x => x.PluginName).Returns(functionView.PluginName);
        return mockFunction;
    }
}

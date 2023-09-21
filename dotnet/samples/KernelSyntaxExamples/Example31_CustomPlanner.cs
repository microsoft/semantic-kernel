// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Threading.Tasks;
using System.Xml;
using System.Xml.XPath;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Plugins.Core;
using Microsoft.SemanticKernel.Plugins.Web;
using Microsoft.SemanticKernel.Plugins.Web.Bing;

using RepoUtils;

// ReSharper disable CommentTypo
// ReSharper disable once InconsistentNaming
internal static class Example31_CustomPlanner
{
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Custom Planner - Create and Execute Markup Plan ========");
        IKernel kernel = InitializeKernel();

        // ContextQuery is part of the QASkill
        IDictionary<string, ISKFunction> skills = LoadQASkill(kernel);
        SKContext context = CreateContextQueryContext(kernel);

        // Create a memory store using the VolatileMemoryStore and the embedding generator registered in the kernel
        kernel.ImportPlugin(new TextMemoryPlugin(kernel.Memory));

        // Setup defined memories for recall
        await RememberFactsAsync(kernel);

        // MarkupSkill named "markup"
        var markup = kernel.ImportPlugin(new MarkupSkill(), "markup");

        // contextQuery "Who is my president? Who was president 3 years ago? What should I eat for dinner" | markup
        // Create a plan to execute the ContextQuery and then run the markup skill on the output
        var plan = new Plan("Execute ContextQuery and then RunMarkup");
        plan.AddSteps(skills["ContextQuery"], markup["RunMarkup"]);

        // Execute plan
        context.Variables.Update("Who is my president? Who was president 3 years ago? What should I eat for dinner");
        var result = await plan.InvokeAsync(context);

        Console.WriteLine("Result:");
        Console.WriteLine(result.GetValue<string>());
        Console.WriteLine();
    }
    /* Example Output
    ======== Custom Planner - Create and Execute Markup Plan ========
    Markup:
    <response><lookup>Who is United States President</lookup><fact>Joe Biden was president 3 years ago</fact><opinion>For dinner, you might enjoy some sushi with your partner, since you both like it and you only ate it once this month</opinion></response>

    Original plan:
        Goal: Run a piece of xml markup

        Steps:
        Goal: response

        Steps:
        - bing.SearchAsync INPUT='Who is United States President' => markup.SearchAsync.result    - Microsoft.SemanticKernel.Planning.Plan. INPUT='Joe Biden was president 3 years ago' => markup.fact.result    - Microsoft.SemanticKernel.Planning.Plan. INPUT='For dinner, you might enjoy some sushi with your partner, since you both like it and you only ate it once this month' => markup.opinion.result

    Result:
    The president of the United States ( POTUS) [A] is the head of state and head of government of the United States of America. The president directs the executive branch of the federal government and is the commander-in-chief of the United States Armed Forces .
    Joe Biden was president 3 years ago
    For dinner, you might enjoy some sushi with your partner, since you both like it and you only ate it once this month
    */

    private static SKContext CreateContextQueryContext(IKernel kernel)
    {
        var context = kernel.CreateNewContext();
        context.Variables.Set("firstname", "Jamal");
        context.Variables.Set("lastname", "Williams");
        context.Variables.Set("city", "Tacoma");
        context.Variables.Set("state", "WA");
        context.Variables.Set("country", "USA");
        context.Variables.Set("collection", "contextQueryMemories");
        context.Variables.Set("limit", "5");
        context.Variables.Set("relevance", "0.3");
        return context;
    }

    private static async Task RememberFactsAsync(IKernel kernel)
    {
        kernel.ImportPlugin(new TextMemoryPlugin(kernel.Memory));

        List<string> memoriesToSave = new()
        {
            "I like pizza and chicken wings.",
            "I ate pizza 10 times this month.",
            "I ate chicken wings 3 time this month.",
            "I ate sushi 1 time this month.",
            "My partner likes sushi and chicken wings.",
            "I like to eat dinner with my partner.",
            "I am a software engineer.",
            "I live in Tacoma, WA.",
            "I have a dog named Tully.",
            "I have a cat named Butters.",
        };

        foreach (var memoryToSave in memoriesToSave)
        {
            await kernel.Memory.SaveInformationAsync("contextQueryMemories", memoryToSave, Guid.NewGuid().ToString());
        }
    }

    // ContextQuery is part of the QASkill
    // DependsOn: TimePlugin named "time"
    // DependsOn: BingSkill named "bing"
    private static IDictionary<string, ISKFunction> LoadQASkill(IKernel kernel)
    {
        string folder = RepoFiles.SampleSkillsPath();
        kernel.ImportPlugin(new TimePlugin(), "time");
#pragma warning disable CA2000 // Dispose objects before losing scope
        var bing = new WebSearchEnginePlugin(new BingConnector(TestConfiguration.Bing.ApiKey));
#pragma warning restore CA2000 // Dispose objects before losing scope
        var search = kernel.ImportPlugin(bing, "bing");

        return kernel.ImportSemanticPluginFromDirectory(folder, "QASkill");
    }

    private static IKernel InitializeKernel()
    {
        return new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureChatCompletionService(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey)
            .WithAzureTextEmbeddingGenerationService(
                TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey)
            .WithMemoryStorage(new VolatileMemoryStore())
            .Build();
    }
}

// Example Skill that can process XML Markup created by ContextQuery
public class MarkupSkill
{
    [SKFunction, Description("Run Markup")]
    public async Task<string> RunMarkupAsync(string docString, SKContext context, IKernel kernel)
    {
        var plan = docString.FromMarkup("Run a piece of xml markup", context);

        Console.WriteLine("Markup plan:");
        Console.WriteLine(plan.ToPlanWithGoalString());
        Console.WriteLine();

        var result = await plan.InvokeAsync(kernel);
        return result.GetValue<string>()!;
    }
}

public static class XmlMarkupPlanParser
{
    private static readonly Dictionary<string, KeyValuePair<string, string>> s_skillMapping = new()
    {
        { "lookup", new KeyValuePair<string, string>("bing", "SearchAsync") },
    };

    public static Plan FromMarkup(this string markup, string goal, SKContext context)
    {
        Console.WriteLine("Markup:");
        Console.WriteLine(markup);
        Console.WriteLine();

        var doc = new XmlMarkup(markup);
        var nodes = doc.SelectElements();
        return nodes.Count == 0 ? new Plan(goal) : NodeListToPlan(nodes, context, goal);
    }

    private static Plan NodeListToPlan(XmlNodeList nodes, SKContext context, string description)
    {
        Plan plan = new(description);
        for (var i = 0; i < nodes.Count; ++i)
        {
            var node = nodes[i];
            var functionName = node!.LocalName;
            var skillName = string.Empty;

            if (s_skillMapping.TryGetValue(node!.LocalName, out KeyValuePair<string, string> value))
            {
                functionName = value.Value;
                skillName = value.Key;
            }

            var hasChildElements = node.HasChildElements();

            if (hasChildElements)
            {
                plan.AddSteps(NodeListToPlan(node.ChildNodes, context, functionName));
            }
            else
            {
                if (string.IsNullOrEmpty(skillName)
                        ? !context.Functions!.TryGetFunction(functionName, out var _)
                        : !context.Functions!.TryGetFunction(skillName, functionName, out var _))
                {
                    var planStep = new Plan(node.InnerText);
                    planStep.Parameters.Update(node.InnerText);
                    planStep.Outputs.Add($"markup.{functionName}.result");
                    plan.Outputs.Add($"markup.{functionName}.result");
                    plan.AddSteps(planStep);
                }
                else
                {
                    var command = string.IsNullOrEmpty(skillName)
                        ? context.Functions.GetFunction(functionName)
                        : context.Functions.GetFunction(skillName, functionName);
                    var planStep = new Plan(command);
                    planStep.Parameters.Update(node.InnerText);
                    planStep.Outputs.Add($"markup.{functionName}.result");
                    plan.Outputs.Add($"markup.{functionName}.result");
                    plan.AddSteps(planStep);
                }
            }
        }

        return plan;
    }
}

#region Utility Classes

public class XmlMarkup
{
    public XmlMarkup(string response, string? wrapperTag = null)
    {
        if (!string.IsNullOrEmpty(wrapperTag))
        {
            response = $"<{wrapperTag}>{response}</{wrapperTag}>";
        }

        this.Document = new XmlDocument();
        this.Document.LoadXml(response);
    }

    public XmlDocument Document { get; }

    public XmlNodeList SelectAllElements()
    {
        return this.Document.SelectNodes("//*")!;
    }

    public XmlNodeList SelectElements()
    {
        return this.Document.SelectNodes("/*")!;
    }
}

#pragma warning disable CA1815 // Override equals and operator equals on value types
public struct XmlNodeInfo
{
    public int StackDepth { get; set; }
    public XmlNode Parent { get; set; }
    public XmlNode Node { get; set; }

    public static implicit operator XmlNode(XmlNodeInfo info)
    {
        return info.Node;
    }
}
#pragma warning restore CA1815

#pragma warning disable CA1711
public static class XmlEx
{
    public static bool HasChildElements(this XmlNode elt)
    {
        if (!elt.HasChildNodes)
        {
            return false;
        }

        var childNodes = elt.ChildNodes;
        for (int i = 0, count = childNodes.Count; i < count; ++i)
        {
            if (childNodes[i]?.NodeType == XmlNodeType.Element)
            {
                return true;
            }
        }

        return false;
    }

    /// <summary>
    ///     Walks the Markup DOM using an XPathNavigator, allowing recursive descent WITHOUT requiring a Stack Hit
    ///     This is safe for very large and highly nested documents.
    /// </summary>
    public static IEnumerable<XmlNodeInfo> EnumerateNodes(this XmlNode node, int maxStackDepth = 32)
    {
        var nav = node.CreateNavigator();
        return EnumerateNodes(nav!, maxStackDepth);
    }

    public static IEnumerable<XmlNodeInfo> EnumerateNodes(this XmlDocument doc, int maxStackDepth = 32)
    {
        var nav = doc.CreateNavigator();
        nav!.MoveToRoot();
        return EnumerateNodes(nav, maxStackDepth);
    }

    public static IEnumerable<XmlNodeInfo> EnumerateNodes(this XPathNavigator nav, int maxStackDepth = 32)
    {
        var info = new XmlNodeInfo
        {
            StackDepth = 0
        };
        var hasChildren = nav.HasChildren;
        while (true)
        {
            info.Parent = (XmlNode)nav.UnderlyingObject!;
            if (hasChildren && info.StackDepth < maxStackDepth)
            {
                nav.MoveToFirstChild();
                info.StackDepth++;
            }
            else
            {
                var hasParent = false;
                while (hasParent = nav.MoveToParent())
                {
                    info.StackDepth--;
                    if (info.StackDepth == 0)
                    {
                        hasParent = false;
                        break;
                    }

                    if (nav.MoveToNext())
                    {
                        break;
                    }
                }

                if (!hasParent)
                {
                    break;
                }
            }

            do
            {
                info.Node = (XmlNode)nav.UnderlyingObject!;
                yield return info;
                if (hasChildren = nav.HasChildren)
                {
                    break;
                }
            } while (nav.MoveToNext());
        }
    }
}
#pragma warning restore CA1711

#endregion Utility Classes

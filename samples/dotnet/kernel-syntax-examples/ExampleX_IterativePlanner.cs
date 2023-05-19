// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Skills.Grpc.Extensions;
using Microsoft.SemanticKernel.Skills.Web.Bing;
using Microsoft.SemanticKernel.Skills.Web.Google;
using Microsoft.SemanticKernel.Skills.Web;
using Planning.IterativePlanner;
using RepoUtils;

/**
 * This example shows how to use gRPC skills.
 */

// ReSharper disable once InconsistentNaming
public static class ExampleX_IterativePlanner
{
    public static async Task RunAsync()
    {
        var kernel = GetKernel();

        //using var googleConnector = new GoogleConnector(Env.Var("GOOGLE_API_KEY"), Env.Var("GOOGLE_SEARCH_ENGINE_ID"));
        using var bingConnector = new BingConnector(Env.Var("BING_API_KEY"));

        var webSearchEngineSkill = new WebSearchEngineSkill(bingConnector);

        kernel.ImportSkill(webSearchEngineSkill, "WebSearch");

        kernel.ImportSkill(new LanguageCalculatorSkill(kernel), "calculator");

        string goal = "Who is Leo DiCaprio's girlfriend? What is her current age raised to the 0.43 power?";
        // result Result :Camila Morrone's age raised to the 0.43 power is approximately 4
        //string goal =  "Who is the current president of the United States? What is his current age divided by 2";
        //using bing :)
        //Result :Joe Biden's age divided by 2 is 39, which is the same as the number of years he has been in politics!

        MrklPlannerText planer = new MrklPlannerText(kernel, 5);
        var result = await planer.ExecutePlanAsync(goal);

        Console.WriteLine("Result :" + result);

        Console.ReadLine();
    }

    private static IKernel GetKernel()
    {
        var kernel = new KernelBuilder()
            //.WithLogger(ConsoleLogger.Log)
            .Build();

        kernel.Config.AddAzureTextCompletionService(
            Env.Var("AZURE_OPENAI_DEPLOYMENT_NAME"),
            Env.Var("AZURE_OPENAI_ENDPOINT"),
            Env.Var("AZURE_OPENAI_KEY")
        );

        return kernel;
    }
}

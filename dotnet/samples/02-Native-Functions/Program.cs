// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Plugins.OrchestratorPlugin;

using ILoggerFactory loggerFactory = LoggerFactory.Create(builder =>
{
    builder
        .SetMinimumLevel(0)
        .AddDebug();
});
var logger = loggerFactory.CreateLogger<Kernel>();

IKernel kernel = new KernelBuilder()
    .WithCompletionService()
    .WithLogger(logger)
    .Build();

var pluginsDirectory = Path.Combine(System.IO.Directory.GetCurrentDirectory(), "plugins");

// Import the semantic functions
kernel.ImportSemanticSkillFromDirectory(pluginsDirectory, "OrchestratorPlugin");
kernel.ImportSemanticSkillFromDirectory(pluginsDirectory, "SummarizePlugin");

// Import the native functions
var mathPlugin = kernel.ImportSkill(new Plugins.MathPlugin.Math(), "MathPlugin");
var orchestratorPlugin = kernel.ImportSkill(new Orchestrator(kernel), "OrchestratorPlugin");

// Make a request that runs the Sqrt function
var result1 = await orchestratorPlugin["RouteRequest"].InvokeAsync("What is the square root of 634?");
Console.WriteLine(result1);

// Make a request that runs the Add function
var result2 = await orchestratorPlugin["RouteRequest"].InvokeAsync("What is 42 plus 1513?");
Console.WriteLine(result2);

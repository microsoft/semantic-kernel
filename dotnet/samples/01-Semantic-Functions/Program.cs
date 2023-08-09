// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;

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

// Import the OrchestratorPlugin and SummarizeSkill from the plugins directory.
var orchestrationPlugin = kernel.ImportSemanticSkillFromDirectory(pluginsDirectory, "OrchestratorPlugin");
var summarizationPlugin = kernel.ImportSemanticSkillFromDirectory(pluginsDirectory, "SummarizePlugin");

// Create a new context and set the input, history, and options variables.
var variables = new ContextVariables
{
    ["input"] = "Yes",
    ["history"] = @"Bot: How can I help you?
User: My team just hit a major milestone and I would like to send them a message to congratulate them.
Bot:Would you like to send an email?",
    ["options"] = "SendEmail, ReadEmail, SendMeeting, RsvpToMeeting, SendChat"
};

// Run the Summarize function with the context.
var result = await kernel.RunAsync(variables, orchestrationPlugin["GetIntent"]);

Console.WriteLine(result);

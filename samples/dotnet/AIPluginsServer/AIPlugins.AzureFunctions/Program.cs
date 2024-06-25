// Copyright (c) Microsoft. All rights reserved.

using System;
using AIPlugins.AzureFunctions.Extensions;
using AIPlugins.AzureFunctions.LinkedIn;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;

const string DefaultSemanticSkillsFolder = "skills";
string semanticSkillsFolder = Environment.GetEnvironmentVariable("SEMANTIC_SKILLS_FOLDER") ?? DefaultSemanticSkillsFolder;

var host = new HostBuilder()
    .ConfigureFunctionsWorkerDefaults()
    .ConfigureServices(services =>
    {
        services
            .AddScoped<IKernel>((providers) =>
            {
                // This will be called each time a new Kernel is needed

                // Get a logger instance
                ILogger<IKernel> logger = providers
                    .GetRequiredService<ILoggerFactory>()
                    .CreateLogger<IKernel>();

                KernelBuilder builder = Kernel.Builder
                    .WithLogger(logger);

                // Register your AI Providers...

                var kernel = builder.Build();

                // Load your skills...
                kernel.ImportSkill(new LinkedInSkill());
                //kernel.RegisterSemanticSkills(semanticSkillsFolder, logger);

                return kernel;
            })
            .AddScoped<IAIPluginRunner, KernelAIPluginRunner>();
    })
    .Build();

host.Run();

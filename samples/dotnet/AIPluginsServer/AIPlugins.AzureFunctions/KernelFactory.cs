// Copyright (c) Microsoft. All rights reserved.

using System;
using AIPlugins.AzureFunctions.SKExtensions;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;

namespace AIPlugins.AzureFunctions;
internal class KernelFactory : IKernelFactory
{
    private const string DefaultSemanticSkillsFolder = "skills";
    private readonly string _semanticSkillsFolder;

    private ILoggerFactory _loggerFactory;

    public KernelFactory(ILoggerFactory loggerFactory)
    {
        this._loggerFactory = loggerFactory;
        this._semanticSkillsFolder = Environment.GetEnvironmentVariable("SEMANTIC_SKILLS_FOLDER") ?? DefaultSemanticSkillsFolder;
    }

    public IKernel CreateKernel()
    {
        ILogger<IKernel> logger = this._loggerFactory.CreateLogger<IKernel>();

        KernelBuilder builder = Kernel.Builder
            .WithLogger(logger);

        // Register your AI Providers...

        var kernel = builder.Build();

        // Load your skills...
        kernel.RegisterSemanticSkills(this._semanticSkillsFolder, logger);

        return kernel;
    }
}

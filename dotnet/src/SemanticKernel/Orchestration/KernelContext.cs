// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.TemplateEngine;

namespace Microsoft.SemanticKernel.Orchestration;
internal sealed class KernelContext : IKernelContext, IDisposable
{
    private Kernel _kernel;

    public ILoggerFactory LoggerFactory => this._kernel.LoggerFactory;

    public IReadOnlySkillCollection Skills => this._kernel.Skills;

    internal KernelContext(
        IReadOnlySkillCollection skillCollection,
        IAIServiceProvider aiServiceProvider,
        IPromptTemplateEngine promptTemplateEngine,
        ISemanticTextMemory memory,
        IDelegatingHandlerFactory httpHandlerFactory,
        ILoggerFactory loggerFactory)
    {
        this._kernel = new Kernel(
            new SkillCollection(skillCollection),
            aiServiceProvider,
            promptTemplateEngine,
            memory,
            httpHandlerFactory,
            loggerFactory);
    }

    public Task<SKContext> RunAsync(ContextVariables variables, CancellationToken cancellationToken = default, params ISKFunction[] pipeline)
    {
        return this._kernel.RunAsync(variables, cancellationToken, pipeline);
    }

    public void Dispose()
    {
        this._kernel.Dispose();
    }

    public SKContext CreateNewContext(ContextVariables? variables = null, IReadOnlySkillCollection? skills = null)
        => this._kernel.CreateNewContext(variables, skills);
}

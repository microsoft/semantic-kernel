// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.SkillDefinition;
using System.Threading.Tasks;
using System.Threading;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Services;
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
            this.GetEditableSkillCollection(skillCollection),
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

    private SkillCollection GetEditableSkillCollection(IReadOnlySkillCollection readOnlyCollection)
    {
        var editableSkillCollection = new SkillCollection();
        foreach (var functionView in readOnlyCollection.GetFunctionViews())
        {
            editableSkillCollection.AddFunction(readOnlyCollection.GetFunction(functionView.SkillName, functionView.Name));
        }

        return editableSkillCollection;
    }

    public SKContext CreateNewContext(ContextVariables? variables = null, IReadOnlySkillCollection? skills = null)
        => this._kernel.CreateNewContext(variables, skills);
}

// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using HandlebarsDotNet;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.PromptTemplate.Handlebars;

internal sealed class HandlebarsPromptTemplate : IPromptTemplate
{
    /// <summary>
    /// Constructor for PromptTemplate.
    /// </summary>
    /// <param name="promptConfig">Prompt template configuration</param>
    /// <param name="loggerFactory">Logger factory</param>
    public HandlebarsPromptTemplate(PromptTemplateConfig promptConfig, ILoggerFactory? loggerFactory = null)
    {
        this._loggerFactory = loggerFactory ?? NullLoggerFactory.Instance;
        this._logger = this._loggerFactory.CreateLogger(typeof(HandlebarsPromptTemplate));
        this._promptModel = promptConfig;
    }

    /// <inheritdoc/>
    public async Task<string> RenderAsync(Kernel kernel, KernelArguments? arguments = null, CancellationToken cancellationToken = default)
    {
        var handlebars = HandlebarsDotNet.Handlebars.Create();

        foreach (IKernelPlugin plugin in kernel.Plugins)
        {
            foreach (KernelFunction function in plugin)
            {
                handlebars.RegisterHelper($"{plugin.Name}_{function.Name}", (writer, hcontext, parameters) =>
                {
                    var result = function.InvokeAsync(kernel, arguments).GetAwaiter().GetResult();
                    writer.WriteSafeString(result.ToString());
                });
            }
        }

        var template = handlebars.Compile(this._promptModel.Template);

        var prompt = template(this.GetVariables(arguments));

        return await Task.FromResult(prompt).ConfigureAwait(true);
    }

    #region private
    private readonly ILoggerFactory _loggerFactory;
    private readonly ILogger _logger;
    private readonly PromptTemplateConfig _promptModel;

    private Dictionary<string, string> GetVariables(KernelArguments? arguments)
    {
        Dictionary<string, string> result = new();

        foreach (var p in this._promptModel.InputParameters)
        {
            if (!string.IsNullOrEmpty(p.DefaultValue))
            {
                result[p.Name] = p.DefaultValue;
            }
        }

        if (arguments == null)
        {
            return result;
        }

        foreach (var kvp in arguments)
        {
            result[kvp.Key] = kvp.Value;
        }

        return result;
    }
    #endregion
}

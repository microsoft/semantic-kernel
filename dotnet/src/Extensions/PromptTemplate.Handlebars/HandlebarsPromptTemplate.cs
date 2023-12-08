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
#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
    public async Task<string> RenderAsync(Kernel kernel, KernelArguments? arguments = null, CancellationToken cancellationToken = default)
#pragma warning restore CS1998
    {
        var handlebars = HandlebarsDotNet.Handlebars.Create();

        foreach (KernelPlugin plugin in kernel.Plugins)
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

        return template(this.GetVariables(arguments));
    }

    #region private
    private readonly ILoggerFactory _loggerFactory;
    private readonly ILogger _logger;
    private readonly PromptTemplateConfig _promptModel;

    private Dictionary<string, object?> GetVariables(KernelArguments? arguments)
    {
        Dictionary<string, object?> result = new();

        foreach (var p in this._promptModel.InputVariables)
        {
            if (!string.IsNullOrEmpty(p.Default))
            {
                result[p.Name] = p.Default;
            }
        }

        if (arguments is not null)
        {
            foreach (var kvp in arguments)
            {
                if (kvp.Value is not null)
                {
                    result[kvp.Key] = kvp.Value;
                }
            }
        }

        return result;
    }
    #endregion
}

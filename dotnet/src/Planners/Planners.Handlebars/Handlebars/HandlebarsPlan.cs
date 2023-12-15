// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using HandlebarsDotNet;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;

namespace Microsoft.SemanticKernel.Planning.Handlebars;

/// <summary>
/// Represents a Handlebars plan.
/// </summary>
public sealed class HandlebarsPlan
{
    /// <summary>
    /// Error message for hallucinated helpers (helpers that are not registered kernel functions or built-in library helpers).
    /// </summary>
    internal const string HallucinatedHelpersErrorMessage = "Template references a helper that cannot be resolved.";

    /// <summary>
    /// The handlebars template representing the plan.
    /// </summary>
    private readonly string _template;

    /// <summary>
    /// Gets the prompt template used to generate the plan.
    /// </summary>
    public string? Prompt { get; set; } = null;

    /// <summary>
    /// Initializes a new instance of the <see cref="HandlebarsPlan"/> class.
    /// </summary>
    /// <param name="generatedPlan">A Handlebars template representing the generated plan.</param>
    /// <param name="createPlanPromptTemplate">Prompt template used to generate the plan.</param>
    public HandlebarsPlan(string generatedPlan, string? createPlanPromptTemplate = null)
    {
        this._template = generatedPlan;
        this.Prompt = createPlanPromptTemplate;
    }

    /// <summary>
    /// Print the generated plan, aka handlebars template that was the create plan chat completion result.
    /// </summary>
    /// <returns>Handlebars template representing the plan.</returns>
    public override string ToString()
    {
        return this._template;
    }

    /// <summary>
    /// Invokes the Handlebars plan.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="arguments">The arguments.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The plan result.</returns>
    public Task<string> InvokeAsync(
        Kernel kernel,
        KernelArguments arguments,
        CancellationToken cancellationToken = default)
    {
        var logger = kernel.LoggerFactory.CreateLogger(typeof(HandlebarsPlan)) ?? NullLogger.Instance;

        return PlannerInstrumentation.InvokePlanAsync(
            static (HandlebarsPlan plan, Kernel kernel, KernelArguments arguments, CancellationToken cancellationToken)
                => plan.InvokeCoreAsync(kernel, arguments, cancellationToken),
            this, kernel, arguments, logger, cancellationToken);
    }

    private async Task<string> InvokeCoreAsync(
        Kernel kernel,
        KernelArguments? arguments = null,
        CancellationToken cancellationToken = default)
    {
        var templateFactory = new HandlebarsPromptTemplateFactory(options: HandlebarsPlanner.PromptTemplateOptions);
        var promptTemplateConfig = new PromptTemplateConfig()
        {
            Template = this._template,
            TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat,
            Name = "InvokeHandlebarsPlan",
        };

        var handlebarsTemplate = templateFactory.Create(promptTemplateConfig);
        try
        {
            return await handlebarsTemplate!.RenderAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);
        }
        catch (HandlebarsRuntimeException ex) when (ex.Message.Contains(HallucinatedHelpersErrorMessage))
        {
            var hallucinatedHelpers = ex.Message.Substring(HallucinatedHelpersErrorMessage.Length + 1);
            throw new KernelException($"[{HandlebarsPlannerErrorCodes.HallucinatedHelpers}] The plan references hallucinated helpers: {hallucinatedHelpers}", ex);
        }
    }
}

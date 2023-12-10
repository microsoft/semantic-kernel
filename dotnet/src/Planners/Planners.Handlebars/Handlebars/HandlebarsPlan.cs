// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Planning.Handlebars;

/// <summary>
/// Represents a Handlebars plan.
/// </summary>
public sealed class HandlebarsPlan
{
    /// <summary>
    /// The handlebars template representing the plan.
    /// </summary>
    private readonly string _template;

    /// <summary>
    /// Gets the prompt template used to generate the plan.
    /// </summary>
    public string Prompt { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="HandlebarsPlan"/> class.
    /// </summary>
    /// <param name="generatedPlan">A Handlebars template representing the generated plan.</param>
    /// <param name="createPlanPromptTemplate">Prompt template used to generate the plan.</param>
    public HandlebarsPlan(string generatedPlan, string createPlanPromptTemplate)
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
        var logger = kernel.LoggerFactory.CreateLogger(typeof(HandlebarsPlan));

        return PlannerInstrumentation.InvokePlanAsync(
            static (HandlebarsPlan plan, Kernel kernel, KernelArguments arguments, CancellationToken cancellationToken)
                => plan.InvokeCoreAsync(kernel, arguments, cancellationToken),
            this, kernel, arguments, logger, cancellationToken);
    }

#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
    private async Task<string> InvokeCoreAsync(
#pragma warning restore CS1998 // Async method lacks 'await' operators and will run synchronously
        Kernel kernel,
        KernelArguments arguments,
        CancellationToken cancellationToken = default)
    {
        return HandlebarsTemplateEngineExtensions.Render(kernel, this._template, arguments, cancellationToken);
    }
}

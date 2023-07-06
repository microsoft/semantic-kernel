// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Diagnostics.Metering;

namespace Microsoft.SemanticKernel.Planning.Sequential;

/// <summary>
/// Builder for <see cref="ISequentialPlanner"/>.
/// </summary>
public class SequentialPlannerBuilder
{
    /// <summary>
    /// Initialize a new instance of the <see cref="SequentialPlannerBuilder"/> class.
    /// </summary>
    /// <param name="kernel">The semantic kernel instance.</param>
    public SequentialPlannerBuilder(IKernel kernel)
    {
        this._kernel = kernel;
    }

    /// <summary>
    /// Build a new planner instance using the settings passed so far.
    /// </summary>
    /// <returns>Planner instance.</returns>
    public ISequentialPlanner Build()
    {
        ISequentialPlanner instance = new SequentialPlanner(this._kernel, this._config, this.prompt);

        instance = new InstrumentedSequentialPlanner(instance, this._logger, this._meter);

        return instance;
    }

    /// <summary>
    /// Use the given configuration with the planner to be built.
    /// </summary>
    /// <param name="config">Instance of <see cref="SequentialPlannerConfig"/> planner configuration.</param>
    /// <returns>Updated planner builder including the given configuration.</returns>
    public SequentialPlannerBuilder WithConfiguration(SequentialPlannerConfig config)
    {
        Verify.NotNull(config);
        this._config = config;
        return this;
    }

    /// <summary>
    /// Use the given prompt with the planner to be built.
    /// </summary>
    /// <param name="prompt">Prompt string.</param>
    /// <returns>Updated planner builder including the given prompt.</returns>
    public SequentialPlannerBuilder WithPrompt(string prompt)
    {
        Verify.NotNullOrWhiteSpace(prompt);
        this.prompt = prompt;
        return this;
    }

    /// <summary>
    /// Add a logger to the planner to be built.
    /// </summary>
    /// <param name="logger">Logger to add.</param>
    /// <returns>Updated planner builder including the logger.</returns>
    public SequentialPlannerBuilder WithLogger(ILogger logger)
    {
        Verify.NotNull(logger);
        this._logger = logger;
        return this;
    }

    /// <summary>
    /// Add a meter to the planner to be built.
    /// </summary>
    /// <param name="meter">Meter to add.</param>
    /// <returns>Updated planner builder including the meter.</returns>
    public SequentialPlannerBuilder WithMeter(IMeter meter)
    {
        Verify.NotNull(meter);
        this._meter = meter;
        return this;
    }

    #region private ================================================================================

    private readonly IKernel _kernel;

    private SequentialPlannerConfig? _config = null;
    private string? prompt = null;
    private ILogger? _logger = NullLogger.Instance;
    private IMeter? _meter = NullMeter.Instance;

    #endregion
}

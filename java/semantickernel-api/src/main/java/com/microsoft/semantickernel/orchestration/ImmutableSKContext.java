// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;
// Copyright (c) Microsoft. All rights reserved.

import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;

import reactor.util.annotation.NonNull;
import reactor.util.annotation.Nullable;

import java.util.function.Supplier;

import javax.annotation.CheckReturnValue;

/// <summary>
/// Semantic Kernel context.
/// </summary>memory
public abstract class ImmutableSKContext<T extends ReadOnlySKContext<T>>
        implements ReadOnlySKContext<T> {
    @Nullable private final Supplier<ReadOnlySkillCollection> skills;
    private final ImmutableContextVariables variables;
    @Nullable private final SemanticTextMemory memory;
    /*
    public <T> ImmutableReadOnlySKContext<T> build(
            ReadOnlyContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable Supplier<ReadOnlySkillCollection> skills) {

    }
            return new ImmutableReadOnlySKContext<T>(
                    variables,
                    memory,
                    skills
            );
    )

     */

    @Nullable
    @Override
    public String getResult() {
        return getVariables().getVariables().get(ReadOnlyContextVariables.MAIN_KEY);
    }

    /*
        /// <summary>
        /// Print the processed input, aka the current data after any processing occurred.
        /// </summary>
        /// <returns>Processed input, aka result</returns>
        public string Result => this.Variables.ToString();

        // /// <summary>
        // /// Whether an error occurred while executing functions in the pipeline.
        // /// </summary>
        // public bool ErrorOccurred => this.Variables.ErrorOccurred;

        /// <summary>
        /// Whether an error occurred while executing functions in the pipeline.
        /// </summary>
        public bool ErrorOccurred { get; private set; }

        /// <summary>
        /// Error details.
        /// </summary>
        public string LastErrorDescription { get; private set; } = string.Empty;

        /// <summary>
        /// When an error occurs, this is the most recent exception.
        /// </summary>
        public Exception? LastException { get; private set; }

        /// <summary>
        /// Cancellation token.
        /// </summary>
        public CancellationToken CancellationToken { get; }

        /// <summary>
        /// Shortcut into user data, access variables by name
        /// </summary>
        /// <param name="name">Variable name</param>
        public string this[string name]
        {
            get => this.Variables[name];
            set => this.Variables[name] = value;
        }

        /// <summary>
        /// Call this method to signal when an error occurs.
        /// In the usual scenarios this is also how execution is stopped, e.g. to inform the user or take necessary steps.
        /// </summary>
        /// <param name="errorDescription">Error description</param>
        /// <param name="exception">If available, the exception occurred</param>
        /// <returns>The current instance</returns>
        public SKContext Fail(string errorDescription, Exception? exception = null)
        {
            this.ErrorOccurred = true;
            this.LastErrorDescription = errorDescription;
            this.LastException = exception;
            return this;
        }
    */
    /// <summary>
    /// User variables
    /// </summary>
    @Override
    public ReadOnlyContextVariables getVariables() {
        return variables;
    }

    /*
        /// <summary>
        /// Semantic memory
        /// </summary>
        public ISemanticTextMemory Memory { get; internal set; }

        /// <summary>
        /// Read only skills collection
        /// </summary>
        public IReadOnlySkillCollection? Skills { get; internal set; }

        /// <summary>
        /// Access registered functions by skill + name. Not case sensitive.
        /// The function might be native or semantic, it's up to the caller handling it.
        /// </summary>
        /// <param name="skillName">Skill name</param>
        /// <param name="functionName">Function name</param>
        /// <returns>Delegate to execute the function</returns>
        public ISKFunction Func(string skillName, string functionName)
        {
            Verify.NotNull(this.Skills, "The skill collection hasn't been set");

            if (this.Skills.HasNativeFunction(skillName, functionName))
            {
                return this.Skills.GetNativeFunction(skillName, functionName);
            }

            return this.Skills.GetSemanticFunction(skillName, functionName);
        }

        /// <summary>
        /// App logger
        /// </summary>
        public ILogger Log { get; }
    */

    ImmutableSKContext(ReadOnlyContextVariables variables) {
        this(variables, null, null);
    }

    /// <summary>
    /// Constructor for the context.
    /// </summary>
    /// <param name="variables">Context variables to include in context.</param>
    /// <param name="memory">Semantic text memory unit to include in context.</param>
    /// <param name="skills">Skills to include in context.</param>
    /// <param name="logger">Logger for operations in context.</param>
    /// <param name="cancellationToken">Optional cancellation token for operations in
    // context.</param>
    protected ImmutableSKContext(
            ReadOnlyContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable Supplier<ReadOnlySkillCollection> skills) {
        this.variables = new ImmutableContextVariables(variables.getVariables());

        if (memory != null) {
            this.memory = memory.copy();
        } else {
            this.memory = null;
        }

        this.skills = skills;
    }

    /*
        @CheckReturnValue
        @Override
        public T copy() {
            return new ImmutableReadOnlySKContext(variables, memory, skills);
        }
    */
    @Nullable
    @Override
    public SemanticTextMemory getSemanticMemory() {
        return memory != null ? memory.copy() : null;
    }

    @Nullable
    @Override
    public ReadOnlySkillCollection getSkills() {
        if (skills == null) {
            return null;
        }
        return skills.get();
    }

    /*
    public T build(
            ReadOnlyContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable Supplier<ReadOnlySkillCollection> skills) {
        return (T) new ImmutableReadOnlySKContext(variables,memory,skills);
    }

     */

    @CheckReturnValue
    @Override
    public T setVariable(@NonNull String key, @NonNull String content) {
        return build(variables.setVariable(key, content), memory, skills);
    }

    @CheckReturnValue
    @Override
    public T appendToVariable(@NonNull String key, @NonNull String content) {
        return build(variables.appendToVariable(key, content), memory, skills);
    }

    /// <summary>
    /// Updates the main input text with the new value after a function is complete.
    /// </summary>
    /// <param name="content">The new input value, for the next function in the pipeline, or as a
    // result for the user
    /// if the pipeline reached the end.</param>
    /// <returns>The current instance</returns>
    @CheckReturnValue
    @Override
    public T update(@NonNull String content) {
        return build(variables.update(content), memory, skills);
    }

    @CheckReturnValue
    @Override
    public T update(@NonNull ReadOnlyContextVariables newData) {
        return build(variables.update(newData, true), memory, skills);
    }

    /// <summary>
    /// Updates all the local data with new data, merging the two datasets.
    /// Do not discard old data
    /// </summary>
    /// <param name="newData">New data to be merged</param>
    /// <param name="merge">Whether to merge and keep old data, or replace. False == discard old
    // data.</param>
    /// <returns>The current instance</returns>

    // @CheckReturnValue
    // @Override
    // public ImmutableSKContext update(@NonNull ImmutableContextVariables newData, boolean merge) {
    //    return new ImmutableSKContext(variables.update(newData, merge), memory, skills);
    // }

    /*

    /// <summary>
    /// Print the processed input, aka the current data after any processing occurred.
    /// If an error occurred, prints the last exception message instead.
    /// </summary>
    /// <returns>Processed input, aka result, or last exception message if any</returns>
    public override string ToString()
    {
        return this.ErrorOccurred ? $"Error: {this.LastErrorDescription}" : this.Result;
    }
    */
}

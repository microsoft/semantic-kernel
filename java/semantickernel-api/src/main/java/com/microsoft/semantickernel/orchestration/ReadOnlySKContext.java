// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;
// Copyright (c) Microsoft. All rights reserved.

import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;

import reactor.util.annotation.NonNull;
import reactor.util.annotation.Nullable;

import java.util.function.Supplier;

import javax.annotation.CheckReturnValue;

/**
 * Semantic Kernel context.
 *
 * <p>This is read only, write operations will return a modified result
 */
public interface ReadOnlySKContext<Type extends ReadOnlySKContext<Type>> {

    Type build(
            ReadOnlyContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable Supplier<ReadOnlySkillCollection> skills);

    /** Build a context with the given arguments. */
    /*
        static <T extends ReadOnlySKContext<T>> ReadOnlySKContext<T> build(
                ReadOnlyContextVariables variables,
                @Nullable SemanticTextMemory memory,
                @Nullable Supplier<ReadOnlySkillCollection> skills) {
            return new ImmutableReadOnlySKContext<T>(variables, memory, skills);
        }
    */
    /** Build a context with the given arguments. */
    /*
    static <T extends ReadOnlySKContext<T>> ReadOnlySKContext<T> build(ReadOnlyContextVariables variables) {
        return new ImmutableReadOnlySKContext<T>(variables);
    }

     */
    /** Build a default context. */
    /*
    static <T extends ReadOnlySKContext<T>> ReadOnlySKContext<T> build() {
        return new ImmutableReadOnlySKContext<T>(ReadOnlyContextVariables.build());
    }

     */

    /**
     * Obtain the result of the execution that produced this context. This will be the "input" entry
     * in the variables.
     *
     * @return the "input" entry in the variables
     */
    @Nullable
    String getResult();

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

    /**
     * Return a copy of all variables within the context
     *
     * @return a clone of the variables
     */
    ReadOnlyContextVariables getVariables();

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

    /// <summary>
    /// Constructor for the context.
    /// </summary>
    /// <param name="variables">Context variables to include in context.</param>
    /// <param name="memory">Semantic text memory unit to include in context.</param>
    /// <param name="skills">Skills to include in context.</param>
    /// <param name="logger">Logger for operations in context.</param>
    /// <param name="cancellationToken">Optional cancellation token for operations in
    // context.</param>
    /**
     * Clones the current context
     *
     * @return a copy of this context
     */
    /*
    @CheckReturnValue
    Type copy();

     */

    /** Provides access to the contexts semantic memory */
    @Nullable
    SemanticTextMemory getSemanticMemory();

    /**
     * Provides access to the skills within this context
     *
     * @return
     */
    @Nullable
    ReadOnlySkillCollection getSkills();

    /**
     * Sets the given variable
     *
     * @param key if null defaults to the "input" key
     * @param content
     * @return A clone of this context with the variable modified
     */
    @CheckReturnValue
    Type setVariable(@NonNull String key, @NonNull String content);

    /**
     * Appends data to the given key
     *
     * @param key
     * @param content
     * @return A clone of this context with the variable modified
     */
    @CheckReturnValue
    Type appendToVariable(@NonNull String key, @NonNull String content);

    /**
     * Updates the input entry with the given data
     *
     * @param content
     * @return A clone of this context with the variable modified
     */
    @CheckReturnValue
    Type update(@NonNull String content);

    /**
     * Merges in the given variables. Duplicate keys provided by newData will overwrite existing
     * entries.
     *
     * @param newData
     * @return A clone of this context with the variable modified
     */
    @CheckReturnValue
    Type update(@NonNull ReadOnlyContextVariables newData);

    /// <summary>
    /// Updates all the local data with new data, merging the two datasets.
    /// Do not discard old data
    /// </summary>
    /// <param name="newData">New data to be merged</param>
    /// <param name="merge">Whether to merge and keep old data, or replace. False == discard old
    // data.</param>
    /// <returns>The current instance</returns>

    // @CheckReturnValue
    // SKContext update(@NonNull ImmutableContextVariables newData, boolean merge);

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

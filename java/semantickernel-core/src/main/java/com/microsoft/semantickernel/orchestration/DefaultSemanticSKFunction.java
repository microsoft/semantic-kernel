// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration; // Copyright (c) Microsoft. All rights reserved.

import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.memory.NullMemory;
import com.microsoft.semantickernel.skilldefinition.ParameterView;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;

import reactor.core.publisher.Mono;

import java.util.List;
import java.util.function.Supplier;

import javax.annotation.Nullable;

/// <summary>
/// Standard Semantic Kernel callable function.
/// SKFunction is used to extend one C# <see cref="Delegate"/>, <see cref="Func{T, TResult}"/>, <see
// cref="Action"/>,
/// with additional methods required by the kernel.
/// </summary>
public abstract class DefaultSemanticSKFunction<
                RequestConfiguration, ContextType extends ReadOnlySKContext<ContextType>>
        extends AbstractSkFunction<RequestConfiguration, ContextType>
        implements SKFunction<RequestConfiguration, ContextType> {

    public DefaultSemanticSKFunction(
            DelegateTypes delegateType,
            List<ParameterView> parameters,
            String skillName,
            String functionName,
            String description,
            @Nullable Supplier<ReadOnlySkillCollection> skillCollection) {
        super(delegateType, parameters, skillName, functionName, description, skillCollection);
        // TODO
        // Verify.NotNull(delegateFunction, "The function delegate is empty");
        // Verify.ValidSkillName(skillName);
        // Verify.ValidFunctionName(functionName);
        // Verify.ParametersUniqueness(parameters);
    }

    @Override
    public Mono<ContextType> invokeAsync(
            String input, @Nullable ContextType context, @Nullable RequestConfiguration settings) {
        if (context == null) {
            context =
                    buildContext(
                            SKBuilders.variables().build(),
                            NullMemory.getInstance(),
                            super.skillCollection);
        }

        context = context.update(input);

        return this.invokeAsync(context, settings);
    }
    /*
    /// <inheritdoc/>
    public string Name { get; }

    /// <inheritdoc/>
    public string SkillName { get; }

    /// <inheritdoc/>
    public string Description { get; }

    /// <inheritdoc/>
    public bool IsSemantic { get; }

    /// <inheritdoc/>
    public CompleteRequestSettings RequestSettings
    {
        get { return this._aiRequestSettings; }
    }

    /// <summary>
    /// List of function parameters
    /// </summary>
    public IList<ParameterView> Parameters { get; }

    /// <summary>
    /// Create a native function instance, wrapping a native object method
    /// </summary>
    /// <param name="methodContainerInstance">Object containing the method to invoke</param>
    /// <param name="methodSignature">Signature of the method to invoke</param>
    /// <param name="skillName">SK skill name</param>
    /// <param name="log">Application logger</param>
    /// <returns>SK function instance</returns>
    */

    /*

        /// <inheritdoc/>
        public FunctionView Describe()
        {
            return new FunctionView
            {
                IsSemantic = this.IsSemantic,
                Name = this.Name,
                SkillName = this.SkillName,
                Description = this.Description,
                Parameters = this.Parameters,
            };
        }

        /// <inheritdoc/>
        public Task<SKContext> InvokeAsync(
            string input,
            SKContext? context = null,
            CompleteRequestSettings? settings = null,
            ILogger? log = null,
            CancellationToken? cancel = null)
        {
            if (context == null)
            {
                var cToken = cancel ?? default;
                log ??= NullLogger.Instance;
                context = new SKContext(
                    new ContextVariables(""),
                    NullMemory.Instance,
                    this._skillCollection,
                    log,
                    cToken);
            }

            context.Variables.Update(input);

            return this.InvokeAsync(context, settings, log, cancel);
        }
    */
    /// <inheritdoc/>
    /*
        /// <inheritdoc/>
        public ISKFunction SetDefaultSkillCollection(IReadOnlySkillCollection skills)
        {
            this._skillCollection = skills;
            return this;
        }

        /// <inheritdoc/>
        public ISKFunction SetAIService(Func<ITextCompletion> serviceFactory)
        {
            Verify.NotNull(serviceFactory, "AI LLM service factory is empty");
            this.VerifyIsSemantic();
            this._aiService = serviceFactory.Invoke();
            return this;
        }

        /// <inheritdoc/>
        public ISKFunction SetAIConfiguration(CompleteRequestSettings settings)
        {
            Verify.NotNull(settings, "AI LLM request settings are empty");
            this.VerifyIsSemantic();
            this._aiRequestSettings = settings;
            return this;
        }

        /// <summary>
        /// Dispose of resources.
        /// </summary>
        public void Dispose()
        {
            this.ReleaseUnmanagedResources();
            GC.SuppressFinalize(this);
        }

        /// <summary>
        /// Finalizer.
        /// </summary>
        ~SKFunction()
        {
            this.ReleaseUnmanagedResources();
        }

        #region private

        private readonly DelegateTypes _delegateType;
        private readonly Delegate _function;
        private readonly ILogger _log;
        private IReadOnlySkillCollection? _skillCollection;
        private CompleteRequestSettings _aiRequestSettings = new();

        private struct MethodDetails
        {
            public bool HasSkFunctionAttribute { get; set; }
            public DelegateTypes Type { get; set; }
            public Delegate Function { get; set; }
            public List<ParameterView> Parameters { get; set; }
            public string Name { get; set; }
            public string Description { get; set; }
        }
    */
    /*
    private void ReleaseUnmanagedResources()
    {
        if (this._aiService is not IDisposable disposable) { return; }

        disposable.Dispose();
    }

    /// <summary>
    /// Throw an exception if the function is not semantic, use this method when some logic makes sense only for semantic functions.
    /// </summary>
    /// <exception cref="KernelException"></exception>
    private void VerifyIsSemantic()
    {
        if (this.IsSemantic) { return; }

        this._log.LogError("The function is not semantic");
        throw new KernelException(
            KernelException.ErrorCodes.InvalidFunctionType,
            "Invalid operation, the method requires a semantic function");
    }

    [SuppressMessage("Maintainability", "CA1508:Avoid dead conditional code", Justification = "Delegate.CreateDelegate result can be null")]
    private static bool EqualMethods(
        object? instance,
        MethodInfo userMethod,
        Type delegateDefinition,
        [NotNullWhen(true)] out Delegate? result)
    {
        // Instance methods
        if (instance != null)
        {
            result = Delegate.CreateDelegate(delegateDefinition, instance, userMethod, false);
            if (result != null) { return true; }
        }

        // Static methods
        result = Delegate.CreateDelegate(delegateDefinition, userMethod, false);

        return result != null;
    }

    // Internal event to count (and test) that the correct delegates are invoked
    private static void TraceFunctionTypeCall(DelegateTypes type, ILogger log)
    {
        log.Log(
            LogLevel.Trace,
            new EventId((int)type, $"FuncType{type}"),
            "Executing function type {0}: {1}", (int)type, type.ToString("G"));
    }

    #endregion

     */
}

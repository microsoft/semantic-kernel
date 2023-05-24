// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.skilldefinition.KernelSkillsSupplier;
import com.microsoft.semantickernel.skilldefinition.ParameterView;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;

import reactor.core.publisher.Mono;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

import javax.annotation.Nullable;

/// <summary>
/// Standard Semantic Kernel callable function.
/// SKFunction is used to extend one C# <see cref="Delegate"/>, <see cref="Func{T, TResult}"/>, <see
// cref="Action"/>,
/// with additional methods required by the kernel.
/// </summary>
public class NativeSKFunction extends AbstractSkFunction<Void, SemanticSKContext> {

    private final SKNativeTask<SemanticSKContext> function;

    public NativeSKFunction(
            AbstractSkFunction.DelegateTypes delegateType,
            SKNativeTask<SemanticSKContext> delegateFunction,
            List<ParameterView> parameters,
            String skillName,
            String functionName,
            String description,
            KernelSkillsSupplier skillCollection) {
        super(delegateType, parameters, skillName, functionName, description, skillCollection);
        // TODO
        // Verify.NotNull(delegateFunction, "The function delegate is empty");
        // Verify.ValidSkillName(skillName);
        // Verify.ValidFunctionName(functionName);
        // Verify.ParametersUniqueness(parameters);

        this.function = delegateFunction;
    }

    @Override
    public Class<Void> getType() {
        return Void.class;
    }

    @Override
    public void registerOnKernel(Kernel kernel) {
        // No actions needed
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

    private static class MethodDetails {
        public final boolean hasSkFunctionAttribute;
        public final AbstractSkFunction.DelegateTypes type;
        public final SKNativeTask<SemanticSKContext> function;
        public final List<ParameterView> parameters;
        public final String name;
        public final String description;

        private MethodDetails(
                boolean hasSkFunctionAttribute,
                AbstractSkFunction.DelegateTypes type,
                SKNativeTask<SemanticSKContext> function,
                List<ParameterView> parameters,
                String name,
                String description) {
            this.hasSkFunctionAttribute = hasSkFunctionAttribute;
            this.type = type;
            this.function = function;
            this.parameters = parameters;
            this.name = name;
            this.description = description;
        }
    }

    public static NativeSKFunction fromNativeMethod(
            Method methodSignature,
            Object methodContainerInstance,
            String skillName,
            KernelSkillsSupplier kernelSkillsSupplier) {
        if (skillName == null || skillName.isEmpty()) {
            skillName = ReadOnlySkillCollection.GlobalSkill;
        }

        MethodDetails methodDetails = getMethodDetails(methodSignature, methodContainerInstance);

        // If the given method is not a valid SK function
        if (!methodSignature.isAnnotationPresent(DefineSKFunction.class)) {
            throw new RuntimeException("Not a valid function");
        }

        return new NativeSKFunction(
                methodDetails.type,
                methodDetails.function,
                methodDetails.parameters,
                skillName,
                methodDetails.name,
                methodDetails.description,
                kernelSkillsSupplier);
    }

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
    */

    @Override
    public SemanticSKContext buildContext(
            ContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable ReadOnlySkillCollection skills) {
        return new DefaultSemanticSKContext(variables, memory, skills);
    }

    // Run the native function
    @Override
    protected Mono<SemanticSKContext> invokeAsyncInternal(
            SemanticSKContext context, @Nullable Void settings) {
        return this.function.run(context);
        /*
        TraceFunctionTypeCall(this._delegateType, this._log);

        this.EnsureContextHasSkills(context);

        switch (this._delegateType)
        {
            case DelegateTypes.Void: // 1
            {
                var callable = (Action)this._function;
                callable();
                return context;
            }

            case DelegateTypes.OutString: // 2
            {
                var callable = (Func<string>)this._function;
                context.Variables.Update(callable());
                return context;
            }

            case DelegateTypes.OutTaskString: // 3
            {
                var callable = (Func<Task<string>>)this._function;
                context.Variables.Update(await callable());
                return context;
            }

            case DelegateTypes.InSKContext: // 4
            {
                var callable = (Action<SKContext>)this._function;
                callable(context);
                return context;
            }

            case DelegateTypes.InSKContextOutString: // 5
            {
                var callable = (Func<SKContext, string>)this._function;
                context.Variables.Update(callable(context));
                return context;
            }

            case DelegateTypes.InSKContextOutTaskString: // 6
            {
                var callable = (Func<SKContext, Task<string>>)this._function;
                context.Variables.Update(await callable(context));
                return context;
            }

            case DelegateTypes.ContextSwitchInSKContextOutTaskSKContext: // 7
            {
                var callable = (Func<SKContext, Task<SKContext>>)this._function;
                // Note: Context Switching: allows the function to replace with a new context, e.g. to branch execution path
                context = await callable(context);
                return context;
            }

            case DelegateTypes.InString:
            {
                var callable = (Action<string>)this._function; // 8
                callable(context.Variables.Input);
                return context;
            }

            case DelegateTypes.InStringOutString: // 9
            {
                var callable = (Func<string, string>)this._function;
                context.Variables.Update(callable(context.Variables.Input));
                return context;
            }

            case DelegateTypes.InStringOutTaskString: // 10
            {
                var callable = (Func<string, Task<string>>)this._function;
                context.Variables.Update(await callable(context.Variables.Input));
                return context;
            }

            case DelegateTypes.InStringAndContext: // 11
            {
                var callable = (Action<string, SKContext>)this._function;
                callable(context.Variables.Input, context);
                return context;
            }

            case DelegateTypes.InStringAndContextOutString: // 12
            {
                var callable = (Func<string, SKContext, string>)this._function;
                context.Variables.Update(callable(context.Variables.Input, context));
                return context;
            }

            case DelegateTypes.InStringAndContextOutTaskString: // 13
            {
                var callable = (Func<string, SKContext, Task<string>>)this._function;
                context.Variables.Update(await callable(context.Variables.Input, context));
                return context;
            }

            case DelegateTypes.ContextSwitchInStringAndContextOutTaskContext: // 14
            {
                var callable = (Func<string, SKContext, Task<SKContext>>)this._function;
                // Note: Context Switching: allows the function to replace with a new context, e.g. to branch execution path
                context = await callable(context.Variables.Input, context);
                return context;
            }

            case DelegateTypes.InStringOutTask: // 15
            {
                var callable = (Func<string, Task>)this._function;
                await callable(context.Variables.Input);
                return context;
            }

            case DelegateTypes.InContextOutTask: // 16
            {
                var callable = (Func<SKContext, Task>)this._function;
                await callable(context);
                return context;
            }

            case DelegateTypes.InStringAndContextOutTask: // 17
            {
                var callable = (Func<string, SKContext, Task>)this._function;
                await callable(context.Variables.Input, context);
                return context;
            }

            case DelegateTypes.OutTask: // 18
            {
                var callable = (Func<Task>)this._function;
                await callable();
                return context;
            }

            case DelegateTypes.Unknown:
            default:
                throw new KernelException(
                    KernelException.ErrorCodes.FunctionTypeNotSupported,
                    "Invalid function type detected, unable to execute.");
        }
        */
    }

    /*
      private void EnsureContextHasSkills(SKContext context)
      {
          // If the function is invoked manually, the user might have left out the skill collection
          context.Skills ??= this._skillCollection;
      }
    */
    private static MethodDetails getMethodDetails(
            Method methodSignature, Object methodContainerInstance) {
        // Verify.NotNull(methodSignature, "Method is NULL");

        // String name = methodSignature.getName();
        ArrayList<ParameterView> parameters = new ArrayList<>();

        boolean hasSkFunctionAttribute =
                methodSignature.isAnnotationPresent(DefineSKFunction.class);

        if (!hasSkFunctionAttribute) {
            throw new RuntimeException("method is not annotated with DefineSKFunction");
        }
        DelegateTypes type = getDelegateType(methodSignature);
        SKNativeTask<SemanticSKContext> function =
                getFunction(methodSignature, methodContainerInstance);

        // boolean hasStringParam =
        //    Arrays.asList(methodSignature.getGenericParameterTypes()).contains(String.class);

        String name = methodSignature.getAnnotation(DefineSKFunction.class).name();
        String description = methodSignature.getAnnotation(DefineSKFunction.class).description();

        /*
            TODO SUPPORT FUNCTION INPUT!!!:

              // SKFunctionInput attribute
              SKFunctionInputAttribute? skMainParam = methodSignature
                  .GetCustomAttributes(typeof(SKFunctionInputAttribute), true)
                  .Cast<SKFunctionInputAttribute>()
                  .FirstOrDefault();

              // SKFunctionContextParameter attribute
              IList<SKFunctionContextParameterAttribute> skContextParams = methodSignature
                  .GetCustomAttributes(typeof(SKFunctionContextParameterAttribute), true)
                  .Cast<SKFunctionContextParameterAttribute>().ToList();

              // Handle main string param description, if available/valid
              // Note: Using [SKFunctionInput] is optional
              if (hasStringParam)
              {
                  result.Parameters.Add(skMainParam != null
                      ? skMainParam.ToParameterView() // Use the developer description
                      : new ParameterView { Name = "input", Description = "Input string", DefaultValue = "" }); // Use a default description
              }
              else if (skMainParam != null)
              {
                  // The developer used [SKFunctionInput] on a function that doesn't support a string input
                  throw new KernelException(
                      KernelException.ErrorCodes.InvalidFunctionDescription,
                      "The function doesn't have a string parameter, do not use " + typeof(SKFunctionInputAttribute));
              }

              // Handle named arg passed via the SKContext object
              // Note: "input" is added first to the list, before context params
              // Note: Using [SKFunctionContextParameter] is optional
              result.Parameters.AddRange(skContextParams.Select(x => x.ToParameterView()));

              // Check for param names conflict
              // Note: the name "input" is reserved for the main parameter
              Verify.ParametersUniqueness(result.Parameters);

              result.Description = skFunctionAttribute.Description ?? "";

              log?.LogTrace("Method {0} found", result.Name);
        */
        return new MethodDetails(
                hasSkFunctionAttribute, type, function, parameters, name, description);
    }

    private static SKNativeTask<SemanticSKContext> getFunction(Method method, Object instance) {
        return (contextInput) -> {
            SemanticSKContext context = contextInput.copy();

            List<Object> args =
                    Arrays.stream(method.getParameters())
                            .map(
                                    parameter -> {
                                        if (SemanticSKContext.class.isAssignableFrom(
                                                parameter.getType())) {
                                            return context; // .copy();
                                        } else if (parameter.isAnnotationPresent(
                                                SKFunctionParameters.class)) {
                                            SKFunctionParameters annotation =
                                                    parameter.getAnnotation(
                                                            SKFunctionParameters.class);
                                            String arg =
                                                    context.getVariables().get(annotation.name());
                                            if (arg == null) {
                                                arg = annotation.defaultValue();
                                            }
                                            return arg;
                                        } else {
                                            throw new RuntimeException(
                                                    "Unknown arg " + parameter.getName());
                                        }
                                    })
                            .collect(Collectors.toList());

            Mono mono;
            if (method.getReturnType().isAssignableFrom(Mono.class)) {
                try {
                    mono = (Mono) method.invoke(instance, args.toArray());
                } catch (IllegalAccessException | InvocationTargetException e) {
                    throw new RuntimeException(e);
                }
            } else {
                try {
                    mono = Mono.just(method.invoke(instance, args.toArray()));
                } catch (IllegalAccessException | InvocationTargetException e) {
                    throw new RuntimeException(e);
                }
            }

            return mono.map(
                    it -> {
                        if (it instanceof SKContext) {
                            return it;
                        } else {
                            return context.update((String) it);
                        }
                    });
        };
    }

    // Inspect a method and returns the corresponding delegate and related info
    private static AbstractSkFunction.DelegateTypes getDelegateType(Method method) {
        // TODO ALL TYPES
        if (method.getReturnType().equals(String.class)) {
            return AbstractSkFunction.DelegateTypes.OutString;
        }

        if (method.getReturnType().equals(Mono.class)) {
            return AbstractSkFunction.DelegateTypes.InSKContextOutTaskString;
        }

        throw new RuntimeException("Unknown function type");
        /*
         if (EqualMethods(instance, method, typeof(Action), out Delegate? funcDelegate))
         {
             return (DelegateTypes.Void, funcDelegate, false);
         }

         if (EqualMethods(instance, method, typeof(Func<string>), out funcDelegate))
         {
             return (DelegateTypes.OutString, funcDelegate, false);
         }

         if (EqualMethods(instance, method, typeof(Func<Task<string>>), out funcDelegate!))
         {
             return (DelegateTypes.OutTaskString, funcDelegate, false);
         }

         if (EqualMethods(instance, method, typeof(Action<SKContext>), out funcDelegate!))
         {
             return (DelegateTypes.InSKContext, funcDelegate, false);
         }

         if (EqualMethods(instance, method, typeof(Func<SKContext, string>), out funcDelegate!))
         {
             return (DelegateTypes.InSKContextOutString, funcDelegate, false);
         }

         if (EqualMethods(instance, method, typeof(Func<SKContext, Task<string>>), out funcDelegate!))
         {
             return (DelegateTypes.InSKContextOutTaskString, funcDelegate, false);
         }

         if (EqualMethods(instance, method, typeof(Func<SKContext, Task<SKContext>>), out funcDelegate!))
         {
             return (DelegateTypes.ContextSwitchInSKContextOutTaskSKContext, funcDelegate, false);
         }

         // === string input ==

         if (EqualMethods(instance, method, typeof(Action<string>), out funcDelegate!))
         {
             return (DelegateTypes.InString, funcDelegate, true);
         }

         if (EqualMethods(instance, method, typeof(Func<string, string>), out funcDelegate!))
         {
             return (DelegateTypes.InStringOutString, funcDelegate, true);
         }

         if (EqualMethods(instance, method, typeof(Func<string, Task<string>>), out funcDelegate!))
         {
             return (DelegateTypes.InStringOutTaskString, funcDelegate, true);
         }

         if (EqualMethods(instance, method, typeof(Action<string, SKContext>), out funcDelegate!))
         {
             return (DelegateTypes.InStringAndContext, funcDelegate, true);
         }

         if (EqualMethods(instance, method, typeof(Func<string, SKContext, string>), out funcDelegate!))
         {
             return (DelegateTypes.InStringAndContextOutString, funcDelegate, true);
         }

         if (EqualMethods(instance, method, typeof(Func<string, SKContext, Task<string>>), out funcDelegate!))
         {
             return (DelegateTypes.InStringAndContextOutTaskString, funcDelegate, true);
         }

         if (EqualMethods(instance, method, typeof(Func<string, SKContext, Task<SKContext>>), out funcDelegate!))
         {
             return (DelegateTypes.ContextSwitchInStringAndContextOutTaskContext, funcDelegate, true);
         }

         // == Tasks without output ==

         if (EqualMethods(instance, method, typeof(Func<string, Task>), out funcDelegate!))
         {
             return (DelegateTypes.InStringOutTask, funcDelegate, true);
         }

         if (EqualMethods(instance, method, typeof(Func<SKContext, Task>), out funcDelegate!))
         {
             return (DelegateTypes.InContextOutTask, funcDelegate, false);
         }

         if (EqualMethods(instance, method, typeof(Func<string, SKContext, Task>), out funcDelegate!))
         {
             return (DelegateTypes.InStringAndContextOutTask, funcDelegate, true);
         }

         if (EqualMethods(instance, method, typeof(Func<Task>), out funcDelegate!))
         {
             return (DelegateTypes.OutTask, funcDelegate, false);
         }

         // [SKContext DoSomething(SKContext context)] is not supported, use the async form instead.
         // If you encounter scenarios that require to interact with the context synchronously, please let us know.
         if (EqualMethods(instance, method, typeof(Func<SKContext, SKContext>), out _))
         {
             throw new KernelException(
                 KernelException.ErrorCodes.FunctionTypeNotSupported,
                 $"Function {method.Name} has an invalid signature 'Func<SKContext, SKContext>'. " +
                 "Please use 'Func<SKContext, Task<SKContext>>' instead.");
         }

         throw new KernelException(
             KernelException.ErrorCodes.FunctionTypeNotSupported,
             $"Function {method.Name} has an invalid signature not supported by the kernel");

        */
    }

    /*
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

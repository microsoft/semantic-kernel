---
# These are optional elements. Feel free to remove any of them.
status: accepted
contact: rogerbarreto
date: 2023-05-29
deciders: rogerbarreto, shawncal, stephentoub
consulted:
informed:
---

# Kernel/Function Handlers - Phase 1

## Context and Problem Statement

A Kernel function caller needs to be able to handle/intercept any function execution in the Kernel before and after it was attempted. Allowing it to modify the prompt, abort the execution, or modify the output and many other scenarios as follows:

- Pre-Execution / Function Invoking

  - Get: SKContext
  - Set: Modify input parameters sending to the function
  - Set: Abort/Cancel pipeline execution
  - Set: Skip function execution

- Post-Execution / Function Invoked

  - Get: LLM Model Result (Tokens Usage, Stop Sequence, ...)
  - Get: SKContext
  - Get: Output parameters
  - Set: Modify output parameters content (before returning the output)
  - Set: Cancel pipeline execution
  - Set: Repeat function execution

## Out of Scope (Will be in phase 2)

- Pre-Execution / Function Invoking

  - Get: Rendered Prompt
  - Get: Current settings used
  - Set: Modify the Rendered Prompt

- Post-Execution / Function Invoked
  - Get: Rendered Prompt
  - Get: Current settings used

## Decision Drivers

- Architecture changes and the associated decision making process should be transparent to the community.
- Decision records are stored in the repository and are easily discoverable for teams involved in the various language ports.
- Simple, Extensible and easy to understand.

## Considered Options

1. Callback Registration + Recursive
2. Single Callback
3. Event Based Registration
4. Middleware
5. ISKFunction Event Support Interfaces

## Pros and Cons of the Options

### 1. Callback Registration Recursive Delegate (Kernel, Plan, Function)

- Specified on plan and function level as a configuration be able to specify what are the callback Handlers that will be triggered.

Pros:

- Common pattern for observing and also changing data exposed as parameter into the delegate signature for (Get/Set) scenarios
- Registering a callback gives back the registration object that can be used to cancel the execution of the function in the future.
- Recursive approach, allows to register multiple callbacks for the same event, and also allows to register callbacks on top of pre existing callbacks.

Cons:

- Registrations may use more memory and might not be garbage collected in the recursive approach, only when the function or the plan is disposed.

### 2. Single Callback Delegate (Kernel, Plan, Function)

- Specified on kernel level as a configuration be able to specify what are the callback Handlers that will be triggered.
  - Specified on function creation: As part of the function constructor be able to specify what are the callback Handlers that will be triggered.
  - Specified on function invocation: As part of the function invoke be able to specify what are the callback Handlers as a parameter that will be triggered.

Pros:

- Common pattern for observing and also changing data exposed as parameter into the delegate signature for (Get/Set) scenarios

Cons:

- Limited to only one method observing a specific event (Pre Post and InExecution). - Function When used as parameter, three new parameters would be needed as part of the function. (Specified on function invocation) - Extra Cons on

### 3. Event Base Registration (Kernel only)

Expose events on both IKernel and ISKFunction that the call can can be observing to interact.

Pros:

- Multiple Listeners can registered for the same event
- Listeners can be registered and unregistered at will
- Common pattern (EventArgs) for observing and also changing data exposed as parameter into the event signature for (Get/Set) scenarios

Cons:

- Event handlers are void, making the EventArgs by reference the only way to modify the data.
- Not clear how supportive is this approach for asynchronous pattern/multi threading
- Won't support `ISKFunction.InvokeAsync`

### 4. Middleware (Kernel Only)

Specified on Kernel level, and would only be used using IKernel.RunAsync operation, this pattern would be similar to asp.net core middlewares, running the pipelines with a context and a requestdelegate next for controlling (Pre/Post conditions)

Pros:

- Common pattern for handling Pre/Post Setting/Filtering data

Cons:

- Functions can run on their own instance, middlewares suggest more complexity and the existence of an external container/manager (Kernel) to intercept/observe function calls.

### 5. ISKFunction Event Support Interfaces

    ```csharp
    class Kernel : IKernel
    {
        RunAsync() {
            var functionInvokingArgs = await this.TriggerEvent<FunctionInvokingEventArgs>(this.FunctionInvoking, skFunction, context);

            var functionResult = await skFunction.InvokeAsync(context, cancellationToken: cancellationToken);

            var functionInvokedArgs = await this.TriggerEvent<FunctionInvokedEventArgs>(
                this.FunctionInvoked,
                skFunction,
                context);
        }

        private TEventArgs? TriggerEvent<TEventArgs>(EventHandler<TEventArgs>? eventHandler, ISKFunction function, SKContext context) where TEventArgs : SKEventArgs
        {
            if (eventHandler is null)
            {
                return null;
            }

            if (function is ISKFunctionEventSupport<TEventArgs> supportedFunction)
            {
                var eventArgs = await supportedFunction.PrepareEventArgsAsync(context);
                eventHandler.Invoke(this, eventArgs);
                return eventArgs;
            }

            // Think about allowing to add data with the extra interface.

            // If a function don't support the specific event we can:
            return null; // Ignore or Throw.
            throw new NotSupportedException($"The provided function \"{function.Name}\" does not supports and implements ISKFunctionHandles<{typeof(TEventArgs).Name}>");
        }
    }

    public interface ISKFunctionEventSupport<TEventArgs> where TEventArgs : SKEventArgs
    {
        Task<TEventArgs> PrepareEventArgsAsync(SKContext context, TEventArgs? eventArgs = null);
    }

    class SemanticFunction : ISKFunction,
        ISKFunctionEventSupport<FunctionInvokingEventArgs>,
        ISKFunctionEventSupport<FunctionInvokedEventArgs>
    {

        public FunctionInvokingEventArgs PrepareEventArgsAsync(SKContext context, FunctionInvokingEventArgs? eventArgs = null)
        {
            var renderedPrompt = await this.RenderPromptTemplateAsync(context);
            context.Variables.Set(SemanticFunction.RenderedPromptKey, renderedPrompt);

            return new SemanticFunctionInvokingEventArgs(this.Describe(), context);
            // OR                                                          Metadata Dictionary<string, object>
            return new FunctionInvokingEventArgs(this.Describe(), context, new Dictionary<string, object>() { { RenderedPrompt, renderedPrompt } });
        }

        public FunctionInvokedEventArgs PrepareEventArgsAsync(SKContext context, FunctionInvokedEventArgs? eventArgs = null)
        {
            return Task.FromResult<FunctionInvokedEventArgs>(new SemanticFunctionInvokedEventArgs(this.Describe(), context));
        }
    }

    public sealed class SemanticFunctionInvokedEventArgs : FunctionInvokedEventArgs
    {
        public SemanticFunctionInvokedEventArgs(FunctionDescription functionDescription, SKContext context)
            : base(functionDescription, context)
        {
            _context = context;
            Metadata[RenderedPromptKey] = this._context.Variables[RenderedPromptKey];
        }

        public string? RenderedPrompt => this.Metadata[RenderedPromptKey];

    }

    public sealed class SemanticFunctionInvokingEventArgs : FunctionInvokingEventArgs
    {
        public SemanticFunctionInvokingEventArgs(FunctionDescription functionDescription, SKContext context)
            : base(functionDescription, context)
        {
            _context = context;
        }
        public string? RenderedPrompt => this._context.Variables[RenderedPromptKey];
    }
    ```

### Pros and Cons

Pros:

- `Kernel` is not aware of `SemanticFunction` implementation details or any other `ISKFunction` implementation
- Extensible to show dedicated EventArgs per custom `ISKFunctions` implementation, including prompts for semantic functions
- Extensible to support future events on the Kernel thru the `ISKFunctionEventSupport<NewEvent>` interface
- Functions can have their own EventArgs specialization.
- Interface is optional, so custom `ISKFunctions` can choose to implement it or not

Cons:

- Any custom functions now will have to responsibility implement the `ISKFunctionEventSupport` interface if they want to support events.
- `Kernel` will have to check if the function implements the interface or not, and if not, it will have to throw an exception or ignore the event.
- Functions implementations that once were limited to InvokeAsync now need to be scattered across multiple places and handle the state of the execution related to content that needs to be get at the beginning or at the end of the invocation.

## Main Questions

- Q: Post Execution Handlers should execute right after the LLM result or before the end of the function execution itself?
  A: Currently post execution Handlers are executed after function execution.

- Q: Should Pre/Post Handlers be many (pub/sub) allowing registration/deregistration?
  A: By using the standard .NET event implementation, this already supports multiple registrations as well as deregistrations managed by the caller.

- Q: Setting Handlers on top of pre existing Handlers should be allowed or throw an error?
  A: By using the standard .NET event implementation, the standard behavior will not throw an error and will execute all the registered handlers.

- Q: Setting Handlers on Plans should automatically cascade this Handlers for all the inner steps + overriding existing ones in the process?
  A: Handlers will be triggered before and after each step is executed the same way the Kernel RunAsync pipeline works.

- Q: When a pre function execution handler intents to cancel the execution, should further handlers in the chain be called or not?
  A: Currently the standard .net behavior is to call all the registered handlers. This way function execution will solely depends on the final state of the Cancellation Request after all handlers were called.

## Decision Outcome

Chosen option: **3. Event Base Registration (Kernel only)**

This approach is the simplest and take the benefits of the standard .NET event implementation.

Further changes will be implemented to fully support all the scenarios in phase 2.

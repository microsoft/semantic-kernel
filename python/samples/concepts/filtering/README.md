# Filtering Samples

This directory contains samples demonstrating the Python filter system in Semantic Kernel.

Filters allow you to intercept and modify pipeline execution at specific points. The Python SDK supports three filter types.

## Filter Types

| Filter | Decorator | Purpose |
|--------|-----------|---------|
| **Prompt Rendering** | `@kernel.filter(FilterTypes.PROMPT_RENDERING)` | Intercept before/after prompt is rendered |
| **Function Invocation** | `@kernel.filter(FilterTypes.FUNCTION_INVOCATION)` | Intercept before/after any function call |
| **Auto Function Invoke** | `@kernel.filter(FilterTypes.AUTO_FUNCTION_INVOCATION)` | Control automatic tool calls |

## Samples

### [prompt_filters.py](./prompt_filters.py)

Basic prompt rendering filter. Demonstrates how to inspect and modify prompts before they're sent to the model.

### [function_invocation_filters.py](./function_invocation_filters.py)

Function invocation filter with logging and exception handling. Shows both `kernel.add_filter()` and `@kernel.filter()` decorator registration.

### [function_invocation_filters_stream.py](./function_invocation_filters_stream.py)

Same as above but for **streaming** responses. Use this when working with streaming chat completions.

### [auto_function_invoke_filters.py](./auto_function_invoke_filters.py)

Controls which automatic tool calls are allowed. Demonstrates `context.terminate = True` to skip specific function calls, and `FunctionResultContent` handling.

### [retry_with_filters.py](./retry_with_filters.py)

Implements automatic retry logic using function invocation filters. Retries on failure with a different model.

### [retry_with_different_model.py](./retry_with_different_model.py)

Similar retry pattern but specifically switches to a fallback model on failure.

## Registration

There are two ways to register a filter:

```python
# Method 1: Decorator
@kernel.filter(filter_type=FilterTypes.FUNCTION_INVOCATION)
async def my_filter(context, next):
    await next(context)

# Method 2: Add function
kernel.add_filter("function_invocation", my_filter)
```

Both are equivalent. Use whichever fits your code style.

## Filter Signature

All filters follow the same signature:

```python
async def filter_name(context: <ContextType>, next: Callable) -> None:
    # Code before next filter/function runs
    await next(context)
    # Code after next filter/function runs
```

The `next` callable passes control to the next filter in the chain, then to the actual function. You can skip execution by not calling `await next(context)`.

## Terminating Auto Function Calls

To prevent an auto-invoked function from executing:

```python
@kernel.filter(FilterTypes.AUTO_FUNCTION_INVOCATION)
async def selective_filter(context: AutoFunctionInvocationContext, next):
    if context.function.name == "dangerous_function":
        context.terminate = True  # Skip this function call
        return
    await next(context)
```

package com.microsoft.semantickernel.hooks;

public interface KernelHook {

    default <T extends HookEvent> T dispatch(T event) {
        if (event instanceof FunctionInvokingEventArgs) {
            return (T) preFunctionInvoke((FunctionInvokingEventArgs) event);
        } else if (event instanceof FunctionInvokedEventArgs) {
            return (T) postFunctionInvoke((FunctionInvokedEventArgs) event);
        } else if (event instanceof PromptRenderingEventArgs) {
            return (T) preRenderPrompt((PromptRenderingEventArgs) event);
        } else if (event instanceof PromptRenderedEventArgs) {
            return (T) postRenderPrompt((PromptRenderedEventArgs) event);
        } else {
            return event;
        }
    }


    interface FunctionInvokingHook extends KernelHook {

        FunctionInvokingEventArgs preFunctionInvoke(FunctionInvokingEventArgs arguments);
    }

    default FunctionInvokingEventArgs preFunctionInvoke(FunctionInvokingEventArgs arguments) {
        return arguments;
    }

    interface FunctionInvokedHook extends KernelHook {

        FunctionInvokedEventArgs<?> postFunctionInvoke(FunctionInvokedEventArgs<?> arguments);
    }

    default FunctionInvokedEventArgs<?> postFunctionInvoke(
        FunctionInvokedEventArgs<?> arguments) {
        return arguments;
    }


    interface PromptRenderingHook extends KernelHook {

        PromptRenderingEventArgs preRenderPrompt(PromptRenderingEventArgs arguments);
    }

    default PromptRenderingEventArgs preRenderPrompt(PromptRenderingEventArgs arguments) {
        return arguments;
    }

    interface PromptRenderedHook extends KernelHook {

        PromptRenderedEventArgs postRenderPrompt(PromptRenderedEventArgs arguments);
    }

    default PromptRenderedEventArgs postRenderPrompt(PromptRenderedEventArgs arguments) {
        return arguments;
    }
}

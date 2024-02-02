package com.microsoft.semantickernel.hooks;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.Function;

import javax.annotation.Nullable;

import com.microsoft.semantickernel.hooks.KernelHook.FunctionInvokedHook;
import com.microsoft.semantickernel.hooks.KernelHook.FunctionInvokingHook;
import com.microsoft.semantickernel.hooks.KernelHook.PreChatCompletionHook;
import com.microsoft.semantickernel.hooks.KernelHook.PromptRenderedHook;
import com.microsoft.semantickernel.hooks.KernelHook.PromptRenderingHook;

public class KernelHooks {

    private final Map<String, KernelHook<?>> hooks;

    public KernelHooks() {
        this.hooks = new HashMap<>();
    }

    public KernelHooks(@Nullable KernelHooks kernelHooks) {
        this();
        if (kernelHooks != null) {
            this.hooks.putAll(kernelHooks.getHooks());
        }
    }

    public KernelHooks(Map<String, KernelHook<?>> hooks) {
        this();
        this.hooks.putAll(hooks);
    }

    public UnmodifiableKernelHooks unmodifiableClone() {
        return new UnmodifiableKernelHooks(this);
    }
    
    private Map<String, KernelHook<?>> getHooks() {
        return Collections.unmodifiableMap(hooks);
    }

    public String addFunctionInvokingHook(
        Function<FunctionInvokingEvent, FunctionInvokingEvent> function) {
        return addHook((FunctionInvokingHook) function::apply);
    }

    public String addFunctionInvokedHook(
        Function<FunctionInvokedEvent<?>, FunctionInvokedEvent<?>> function) {
        return addHook((FunctionInvokedHook) function::apply);
    }

    public String addPreChatCompletionHook(
        Function<PreChatCompletionEvent, PreChatCompletionEvent> function) {
        return addHook((PreChatCompletionHook) function::apply);
    }

    public String addPromptRenderedHook(
        Function<PromptRenderedEvent, PromptRenderedEvent> function) {
        return addHook((PromptRenderedHook) function::apply);
    }

    public String addPromptRenderingHook(
        Function<PromptRenderingEvent, PromptRenderingEvent> function) {
        return addHook((PromptRenderingHook) function::apply);
    }

    @SuppressWarnings("unchecked")
    public <T extends KernelHookEvent> T executeHooks(T event) {
        for (KernelHook<?> hook : hooks.values()) {
            if (hook.test(event)) {
                // unchecked cast
                event = ((KernelHook<T>) hook).apply(event);
            }
        }
        return event;
    }

    public String addHook(KernelHook<?> hook) {
        return addHook(UUID.randomUUID().toString(), hook);
    }

    public String addHook(String hookName, KernelHook<?> hook) {
        hooks.put(hookName, hook);
        return hookName;
    }

    public KernelHook<?> removeHook(String hookName) {
        return hooks.remove(hookName);
    }

    public KernelHooks append(@Nullable KernelHooks kernelHooks) {
        if (kernelHooks == null) {
            return this;
        }
        hooks.putAll(kernelHooks.getHooks());

        return this;
    }

    public boolean isEmpty() {
        return hooks.isEmpty();
    }

    public static class UnmodifiableKernelHooks extends KernelHooks {
            
        private UnmodifiableKernelHooks(KernelHooks kernelHooks) {
            super(kernelHooks);
        }

        @Override
        public String addFunctionInvokingHook(Function<FunctionInvokingEvent, FunctionInvokingEvent> function) {
            throw new UnsupportedOperationException("unmodifiable instance of KernelHooks");
        }

        @Override
        public String addFunctionInvokedHook(Function<FunctionInvokedEvent<?>, FunctionInvokedEvent<?>> function) {
            throw new UnsupportedOperationException("unmodifiable instance of KernelHooks");
        }

        @Override
        public String addPreChatCompletionHook(Function<PreChatCompletionEvent, PreChatCompletionEvent> function) {
            throw new UnsupportedOperationException("unmodifiable instance of KernelHooks");
        }

        @Override
        public String addPromptRenderedHook(Function<PromptRenderedEvent, PromptRenderedEvent> function) {
            throw new UnsupportedOperationException("unmodifiable instance of KernelHooks");
        }

        @Override
        public String addPromptRenderingHook(Function<PromptRenderingEvent, PromptRenderingEvent> function) {
            throw new UnsupportedOperationException("unmodifiable instance of KernelHooks");
        }

        @Override
        public String addHook(KernelHook<?> hook) {
            throw new UnsupportedOperationException("unmodifiable instance of KernelHooks");
        }

        @Override
        public String addHook(String hookName, KernelHook<?> hook) {
            throw new UnsupportedOperationException("unmodifiable instance of KernelHooks");
        }

        @Override
        public KernelHooks append(@Nullable KernelHooks kernelHooks) {
            throw new UnsupportedOperationException("unmodifiable instance of KernelHooks");
        }

        @Override
        public KernelHook<?> removeHook(String hookName) {
            throw new UnsupportedOperationException("unmodifiable instance of KernelHooks");
        }
    }


}

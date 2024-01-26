package com.microsoft.semantickernel.hooks;

import com.microsoft.semantickernel.hooks.KernelHook.FunctionInvokedHook;
import com.microsoft.semantickernel.hooks.KernelHook.FunctionInvokingHook;
import com.microsoft.semantickernel.hooks.KernelHook.PreChatCompletionHook;
import com.microsoft.semantickernel.hooks.KernelHook.PromptRenderedHook;
import com.microsoft.semantickernel.hooks.KernelHook.PromptRenderingHook;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.Function;
import javax.annotation.Nullable;

public class KernelHooks {

    private final Map<String, KernelHook<?>> hooks;

    public KernelHooks() {
        this.hooks = new HashMap<>();
    }

    public KernelHooks(@Nullable KernelHooks kernelHooks) {
        if (kernelHooks == null) {
            this.hooks = new HashMap<>();
        } else {
            this.hooks = new HashMap<>(kernelHooks.getHooks());
        }
    }

    public KernelHooks(Map<String, KernelHook<?>> hooks) {
        this.hooks = new HashMap<>(hooks);
    }

    private Map<String, KernelHook<?>> getHooks() {
        return Collections.unmodifiableMap(hooks);
    }

    public String addFunctionInvokingHook(
        Function<FunctionInvokingEvent, FunctionInvokingEvent> function) {
        return addHook((FunctionInvokingHook) function::apply);
    }

    public String addFunctionInvokedHook(
        Function<FunctionInvokedEvent, FunctionInvokedEvent> function) {
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

    public <T extends KernelHookEvent> T executeHooks(T event) {
        for (KernelHook<?> hook : hooks.values()) {
            if (hook.test(event)) {
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

    public KernelHooks append(KernelHooks kernelHooks) {
        Map<String, KernelHook<?>> newHooks = new HashMap<>(this.hooks);
        newHooks.putAll(this.hooks);
        newHooks.putAll(kernelHooks.getHooks());

        return new KernelHooks(newHooks);
    }
}

package com.microsoft.semantickernel.hooks;

import com.microsoft.semantickernel.hooks.KernelHook.FunctionInvokedHook;
import com.microsoft.semantickernel.hooks.KernelHook.FunctionInvokingHook;
import com.microsoft.semantickernel.hooks.KernelHook.PreChatCompletionHook;
import com.microsoft.semantickernel.hooks.KernelHook.PromptRenderedHook;
import com.microsoft.semantickernel.hooks.KernelHook.PromptRenderingHook;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.Function;

public class HookService {

    private final Map<String, KernelHook<?>> hooks = new HashMap<>();

    public void addFunctionInvokingHook(
        Function<FunctionInvokingEventArgs, FunctionInvokingEventArgs> function) {
        addHook((FunctionInvokingHook) function::apply);
    }

    public void addFunctionInvokedHook(
        Function<FunctionInvokedEventArgs, FunctionInvokedEventArgs> function) {
        addHook((FunctionInvokedHook) function::apply);
    }

    public void addPreChatCompletionHook(
        Function<PreChatCompletionHookEvent, PreChatCompletionHookEvent> function) {
        addHook((PreChatCompletionHook) function::apply);
    }

    public void addPromptRenderedHook(
        Function<PromptRenderedEventArgs, PromptRenderedEventArgs> function) {
        addHook((PromptRenderedHook) function::apply);
    }

    public void addPromptRenderingHook(
        Function<PromptRenderingEventArgs, PromptRenderingEventArgs> function) {
        addHook((PromptRenderingHook) function::apply);
    }

    public <T extends HookEvent> T executeHooks(T event) {
        for (KernelHook<?> hook : hooks.values()) {
            if (hook.test(event)) {
                event = ((KernelHook<T>) hook).apply(event);
            }
        }
        return event;
    }

    public String addHook(KernelHook<?> hook) {
        String id = UUID.randomUUID().toString();
        addHook(id, hook);
        return id;
    }

    public void addHook(String hookName, KernelHook<?> hook) {
        hooks.put(hookName, hook);
    }

    public KernelHook removeHook(String hookName) {
        return hooks.remove(hookName);
    }

}

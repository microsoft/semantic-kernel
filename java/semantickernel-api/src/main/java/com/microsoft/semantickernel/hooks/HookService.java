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

public class HookService {

    private final Map<String, KernelHook<?>> hooks;

    public HookService() {
        this.hooks = new HashMap<>();
    }

    public HookService(@Nullable HookService hookService) {
        if (hookService == null) {
            this.hooks = new HashMap<>();
        } else {
            this.hooks = new HashMap<>(hookService.getHooks());
        }
    }

    public HookService(Map<String, KernelHook<?>> hooks) {
        this.hooks = new HashMap<>(hooks);
    }

    private Map<String, KernelHook<?>> getHooks() {
        return Collections.unmodifiableMap(hooks);
    }

    public String addFunctionInvokingHook(
        Function<FunctionInvokingEventArgs, FunctionInvokingEventArgs> function) {
        return addHook((FunctionInvokingHook) function::apply);
    }

    public String addFunctionInvokedHook(
        Function<FunctionInvokedEventArgs, FunctionInvokedEventArgs> function) {
        return addHook((FunctionInvokedHook) function::apply);
    }

    public String addPreChatCompletionHook(
        Function<PreChatCompletionHookEvent, PreChatCompletionHookEvent> function) {
        return addHook((PreChatCompletionHook) function::apply);
    }

    public String addPromptRenderedHook(
        Function<PromptRenderedEventArgs, PromptRenderedEventArgs> function) {
        return addHook((PromptRenderedHook) function::apply);
    }

    public String addPromptRenderingHook(
        Function<PromptRenderingEventArgs, PromptRenderingEventArgs> function) {
        return addHook((PromptRenderingHook) function::apply);
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

    public HookService append(HookService hooks) {
        Map<String, KernelHook<?>> newHooks = new HashMap<>(this.hooks);
        newHooks.putAll(this.hooks);
        newHooks.putAll(hooks.getHooks());

        return new HookService(newHooks);
    }
}

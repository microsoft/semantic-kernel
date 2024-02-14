package com.microsoft.semantickernel.hooks;

import com.microsoft.semantickernel.hooks.KernelHook.FunctionInvokedHook;
import com.microsoft.semantickernel.hooks.KernelHook.FunctionInvokingHook;
import com.microsoft.semantickernel.hooks.KernelHook.PreChatCompletionHook;
import com.microsoft.semantickernel.hooks.KernelHook.PromptRenderedHook;
import com.microsoft.semantickernel.hooks.KernelHook.PromptRenderingHook;

import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Map;
import java.util.SortedSet;
import java.util.TreeSet;
import java.util.UUID;
import java.util.function.Function;

import javax.annotation.Nullable;

/**
 * Represents a collection of hooks that can be used to intercept and modify events in the kernel.
 */
public class KernelHooks {

    private final Map<String, KernelHook<?>> hooks;

    /**
     * Creates a new instance of the {@link KernelHooks} class.
     */
    public KernelHooks() {
        this.hooks = new HashMap<>();
    }

    /**
     * Creates a copy of the {@link KernelHooks}.
     * @param kernelHooks the hooks to copy
     */
    public KernelHooks(@Nullable KernelHooks kernelHooks) {
        this();
        if (kernelHooks != null) {
            this.hooks.putAll(kernelHooks.getHooks());
        }
    }

    /**
     * Creates a new instance of the {@link KernelHooks} class 
     * from the given hooks.
     * @param hooks the hooks to add
     */
    public KernelHooks(Map<String, KernelHook<?>> hooks) {
        this();
        this.hooks.putAll(hooks);
    }

    /**
     * Creates an unmodifiable copy of this {@link KernelHooks}.
     * @return an unmodifiable copy of this {@link KernelHooks}
     */
    public UnmodifiableKernelHooks unmodifiableClone() {
        return new UnmodifiableKernelHooks(this);
    }
    

    /**
     * Gets the hooks in this collection.
     * @return an unmodifiable map of the hooks
     */
    private Map<String, KernelHook<?>> getHooks() {
        return Collections.unmodifiableMap(hooks);
    }

    /**
     * Add a {@link FunctionInvokingHook} to the collection of hooks.
     * @param function the function to add
     * @return the key of the hook in the collection
     */
    public String addFunctionInvokingHook(
        Function<FunctionInvokingEvent<?>, FunctionInvokingEvent<?>> function) {
        return addHook((FunctionInvokingHook) function::apply);
    }

    /**
     * Add a {@link FunctionInvokedHook} to the collection of hooks.
     * @param function the function to add
     * @return the key of the hook in the collection
     */
    public String addFunctionInvokedHook(
        Function<FunctionInvokedEvent<?>, FunctionInvokedEvent<?>> function) {
        return addHook((FunctionInvokedHook) function::apply);
    }

    /**
     * Add a {@link PreChatCompletionHook} to the collection of hooks.
     * @param function the function to add
     * @return the key of the hook in the collection
     */
    public String addPreChatCompletionHook(
        Function<PreChatCompletionEvent, PreChatCompletionEvent> function) {
        return addHook((PreChatCompletionHook) function::apply);
    }

    /**
     * Add a {@link PromptRenderedHook} to the collection of hooks.
     * @param function the function to add
     * @return the key of the hook in the collection
     */
    public String addPromptRenderedHook(
        Function<PromptRenderedEvent, PromptRenderedEvent> function) {
        return addHook((PromptRenderedHook) function::apply);
    }

    /**
     * Add a {@link PromptRenderingHook} to the collection of hooks.
     * @param function the function to add
     * @return the key of the hook in the collection
     */
    public String addPromptRenderingHook(
        Function<PromptRenderingEvent, PromptRenderingEvent> function) {
        return addHook((PromptRenderingHook) function::apply);
    }

    /**
     * Executes the hooks in this collection that accept the event.
     * @param event the event to execute the hooks on
     * @param <T> the type of the event
     * @return the event after the hooks have been executed
     */
    @SuppressWarnings("unchecked")
    public <T extends KernelHookEvent> T executeHooks(T event) {
        SortedSet<KernelHook<?>> hooks = new TreeSet<>(Comparator.comparingInt(KernelHook::getPriority));

        hooks.addAll(this.hooks.values());

        for (KernelHook<?> hook : hooks) {
            if (hook.test(event)) {
                // unchecked cast
                event = ((KernelHook<T>) hook).apply(event);
            }
        }
        return event;
    }

    /**
     * Add a {@link KernelHook} to the collection of hooks.
     * @param hook the hook to add
     * @return the key of the hook in the collection
     */
    public String addHook(KernelHook<?> hook) {
        return addHook(UUID.randomUUID().toString(), hook);
    }

    /**
     * Add a {@link KernelHook} to the collection of hooks.
     * @param hookName the key of the hook in the collection
     * @param hook the hook to add
     * @return the key of the hook in the collection
     */
    public String addHook(String hookName, KernelHook<?> hook) {
        hooks.put(hookName, hook);
        return hookName;
    }

    /**
     * Remove a hook from the collection of hooks.
     * @param hookName the key of the hook in the collection
     * @return the removed hook, or {@code null} if the hook was not found
     */
    public KernelHook<?> removeHook(String hookName) {
        return hooks.remove(hookName);
    }

    /**
     * Appends the given hooks to this collection.
     * @param kernelHooks the hooks to append
     * @return this instance of the {@link KernelHooks} class
     */
    public KernelHooks addHooks(@Nullable KernelHooks kernelHooks) {
        if (kernelHooks == null) {
            return this;
        }
        hooks.putAll(kernelHooks.getHooks());

        return this;
    }

    /**
     * Determines if this collection of hooks is empty.
     * @return {@code true} if the collection is empty, otherwise {@code false}
     */
    public boolean isEmpty() {
        return hooks.isEmpty();
    }

    /**
     * A wrapper for KernelHooks that disables mutating methods.
     */
    public static class UnmodifiableKernelHooks extends KernelHooks {

        private UnmodifiableKernelHooks(KernelHooks kernelHooks) {
            super(kernelHooks);
        }

        @Override
        public String addFunctionInvokingHook(
            Function<FunctionInvokingEvent<?>, FunctionInvokingEvent<?>> function) {
            throw new UnsupportedOperationException("unmodifiable instance of KernelHooks");
        }

        @Override
        public String addFunctionInvokedHook(
            Function<FunctionInvokedEvent<?>, FunctionInvokedEvent<?>> function) {
            throw new UnsupportedOperationException("unmodifiable instance of KernelHooks");
        }

        @Override
        public String addPreChatCompletionHook(
            Function<PreChatCompletionEvent, PreChatCompletionEvent> function) {
            throw new UnsupportedOperationException("unmodifiable instance of KernelHooks");
        }

        @Override
        public String addPromptRenderedHook(
            Function<PromptRenderedEvent, PromptRenderedEvent> function) {
            throw new UnsupportedOperationException("unmodifiable instance of KernelHooks");
        }

        @Override
        public String addPromptRenderingHook(
            Function<PromptRenderingEvent, PromptRenderingEvent> function) {
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
        public KernelHooks addHooks(@Nullable KernelHooks kernelHooks) {
            throw new UnsupportedOperationException("unmodifiable instance of KernelHooks");
        }

        @Override
        public KernelHook<?> removeHook(String hookName) {
            throw new UnsupportedOperationException("unmodifiable instance of KernelHooks");
        }
    }


}

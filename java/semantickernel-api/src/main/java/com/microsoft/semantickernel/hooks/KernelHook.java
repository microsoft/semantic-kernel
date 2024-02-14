package com.microsoft.semantickernel.hooks;

import com.azure.ai.openai.models.ChatCompletionsOptions;
import com.azure.ai.openai.models.ChatRequestMessage;

import java.util.List;
import java.util.function.Function;
import java.util.function.Predicate;

/**
 * Represents a hook that can be used to intercept and modify arguments to {@code KernelFunction}s.
 * A {@code KernelHook} implements a {@code Predicate} that determines if the hook is interested 
 * in a particular event, and a {@code Function} that can be used to modify the event. The 
 * @param <T> The type of the event that the hook is interested in
 */
public interface KernelHook<T extends KernelHookEvent> extends Predicate<KernelHookEvent>,
    Function<T, T> {

    /**
     * The priority of the hook. The default priority is 50. The priority is used to determine the
     * order in which hooks that accept the same event type are executed, lower priorities are executed first. No ordering is
     * guaranteed for hooks with the same priority.
     *
     * @return the priority of the hook
     */
    default int getPriority() {
        return 50;
    }

    /**
     * A hook that accepts {@link FunctionInvokingEvent} 
     */
    interface FunctionInvokingHook extends KernelHook<FunctionInvokingEvent<?>> {

        @Override
        default boolean test(KernelHookEvent arguments) {
            return FunctionInvokingEvent.class.isAssignableFrom(arguments.getClass());
        }
    }

    /**
     * A hook that accepts {@link FunctionInvokedEvent} 
     */
    interface FunctionInvokedHook extends KernelHook<FunctionInvokedEvent<?>> {

        @Override
        default boolean test(KernelHookEvent arguments) {
            return FunctionInvokedEvent.class.isAssignableFrom(arguments.getClass());
        }
    }

    /**
     * A hook that accepts {@link PromptRenderingEvent} 
     */
    interface PromptRenderingHook extends KernelHook<PromptRenderingEvent> {

        @Override
        default boolean test(KernelHookEvent arguments) {
            return PromptRenderingEvent.class.isAssignableFrom(arguments.getClass());
        }
    }

    /**
     * A hook that accepts {@link PromptRenderedEvent} 
     */
    interface PromptRenderedHook extends KernelHook<PromptRenderedEvent> {

        @Override
        default boolean test(KernelHookEvent arguments) {
            return PromptRenderedEvent.class.isAssignableFrom(arguments.getClass());
        }
    }


    /**
     * A hook that accepts {@link PreChatCompletionEvent} 
     */
    interface PreChatCompletionHook extends KernelHook<PreChatCompletionEvent> {

        @Override
        default boolean test(KernelHookEvent arguments) {
            return PreChatCompletionEvent.class.isAssignableFrom(arguments.getClass());
        }

        /**
         * A convenience method to clone the options with the messages from the event.
         * @param options the options to clone
         * @param messages the messages to use
         * @return the new options
         */
        static ChatCompletionsOptions cloneOptionsWithMessages(
            ChatCompletionsOptions options,
            List<ChatRequestMessage> messages) {
            ChatCompletionsOptions newOptions = new ChatCompletionsOptions(messages)
                .setPresencePenalty(options.getPresencePenalty())
                .setFrequencyPenalty(options.getFrequencyPenalty())
                .setLogitBias(options.getLogitBias())
                .setMaxTokens(options.getMaxTokens())
                .setModel(options.getModel())
                .setStop(options.getStop())
                .setTemperature(options.getTemperature())
                .setTools(options.getTools())
                .setTopP(options.getTopP())
                .setUser(options.getUser())
                .setDataSources(options.getDataSources())
                .setEnhancements(options.getEnhancements())
                .setFunctions(options.getFunctions())
                .setN(options.getN())
                .setResponseFormat(options.getResponseFormat())
                .setSeed(options.getSeed())
                .setStream(options.isStream())
                .setToolChoice(options.getToolChoice());

            if (options.getFunctionCall() != null) {
                newOptions = newOptions.setFunctionCall(options.getFunctionCall());
            }
            return newOptions;
        }
    }
}

package com.microsoft.semantickernel.hooks;

import com.azure.ai.openai.models.ChatCompletionsOptions;
import com.azure.ai.openai.models.ChatRequestMessage;
import java.util.List;
import java.util.function.Function;
import java.util.function.Predicate;

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

    interface FunctionInvokingHook extends KernelHook<FunctionInvokingEvent> {

        @Override
        default boolean test(KernelHookEvent arguments) {
            return FunctionInvokingEvent.class.isAssignableFrom(arguments.getClass());
        }
    }

    interface FunctionInvokedHook extends KernelHook<FunctionInvokedEvent> {

        @Override
        default boolean test(KernelHookEvent arguments) {
            return FunctionInvokedEvent.class.isAssignableFrom(arguments.getClass());
        }
    }

    interface PromptRenderingHook extends KernelHook<PromptRenderingEvent> {

        @Override
        default boolean test(KernelHookEvent arguments) {
            return PromptRenderingEvent.class.isAssignableFrom(arguments.getClass());
        }
    }

    interface PromptRenderedHook extends KernelHook<PromptRenderedEvent> {

        @Override
        default boolean test(KernelHookEvent arguments) {
            return PromptRenderedEvent.class.isAssignableFrom(arguments.getClass());
        }
    }

    interface PreChatCompletionHook extends KernelHook<PreChatCompletionEvent> {

        @Override
        default boolean test(KernelHookEvent arguments) {
            return PreChatCompletionEvent.class.isAssignableFrom(arguments.getClass());
        }

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

import { ICompleteRequestSettings } from '../ai';
import { ILogger } from '../utils/logger';
import { ContextVariables, ISKFunction, SKContext } from '.';

export class SKFunctionExtensions {
    /**
     * Configure the LLM settings used by semantic function.
     * @param skFunction Semantic function
     * @param settings Completion settings
     * @returns Self instance
     */
    public static useCompletionSettings(skFunction: ISKFunction, settings: ICompleteRequestSettings): ISKFunction {
        return skFunction.setAIConfiguration(settings);
    }

    /**
     * Change the LLM Max Tokens configuration
     * @param skFunction Semantic function
     * @param maxTokens Tokens count
     * @returns Self instance
     */
    public static useMaxTokens(skFunction: ISKFunction, maxTokens: number): ISKFunction {
        skFunction.requestSettings.maxTokens = maxTokens;
        return skFunction;
    }

    /**
     * Change the LLM Temperature configuration
     * @param skFunction Semantic function
     * @param temperature Temperature value
     * @returns Self instance
     */
    public static useTemperature(skFunction: ISKFunction, temperature: number): ISKFunction {
        skFunction.requestSettings.temperature = temperature;
        return skFunction;
    }

    /**
     * Change the Max Tokens configuration
     * @param skFunction Semantic function
     * @param topP TopP value
     * @returns Self instance
     */
    public static useTopP(skFunction: ISKFunction, topP: number): ISKFunction {
        skFunction.requestSettings.topP = topP;
        return skFunction;
    }

    /**
     * Change the Max Tokens configuration
     * @param skFunction Semantic function
     * @param presencePenalty Presence penalty value
     * @returns Self instance
     */
    public static usePresencePenalty(skFunction: ISKFunction, presencePenalty: number): ISKFunction {
        skFunction.requestSettings.presencePenalty = presencePenalty;
        return skFunction;
    }

    /**
     * Change the Max Tokens configuration
     * @param skFunction Semantic function
     * @param frequencyPenalty Frequency penalty value
     * @returns Self instance
     */
    public static useFrequencyPenalty(skFunction: ISKFunction, frequencyPenalty: number): ISKFunction {
        skFunction.requestSettings.frequencyPenalty = frequencyPenalty;
        return skFunction;
    }

    /**
     * Execute a function with a custom set of context variables.
     * Use case: template engine: semantic function with custom input variable.
     * @param function Function to execute
     * @param input Custom function input
     * @param log App logger
     * @returns The temporary context
     */
    public static async invokeWithCustomInput(
        fn: ISKFunction,
        input: ContextVariables,
        log: ILogger
    ): Promise<SKContext> {
        const tmpContext = new SKContext(input, undefined, log);
        try {
            await fn.invoke(tmpContext);
        } catch (err: any) {
            tmpContext.fail(err.message, err as Error);
        }
        return tmpContext;
    }
}

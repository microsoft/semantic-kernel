/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { ICompleteRequestSettings, ITextCompletionClient } from '../ai';
import { ILogger } from '../utils/logger';
import { IFunctionRegistryReader, FunctionView } from '../registry';
import { SKContext } from './skContext';

/**
 * Semantic Kernel callable function interface
 */
export interface ISKFunction {
    /**
     * Name of the function.
     * @remarks
     * The name is used by the registry and in prompt templates e.g. {{skillName.functionName}}
     */
    readonly name: string;

    /**
     * Name of the skill containing the function.
     * @remarks
     * The name is used by the registry and in prompt templates e.g. {{skillName.functionName}}
     */
    readonly skillName: string;

    /**
     * Function description.
     * @remarks
     * The description is used in combination with embeddings when searching relevant functions.
     */
    readonly description: string;

    /**
     * Whether the function is defined using a prompt template.
     * @remarks
     * IMPORTANT: native functions might use semantic functions internally,
     * so when this property is False, executing the function might still involve AI calls.
     */
    readonly isSemantic: boolean;

    /**
     * AI backend settings
     */
    readonly requestSettings: ICompleteRequestSettings;

    /**
     * Returns a description of the function, including parameters.
     */
    describe(): FunctionView;

    /**
     * Invoke the internal delegate.
     * @param context SK context
     * @param settings LLM completion settings
     * @param log Application logger
     * @returns The updated context, potentially a new one if context switching is implemented.
     */
    invoke(context?: SKContext, settings?: ICompleteRequestSettings, log?: ILogger): Promise<SKContext>;

    /**
     * Invoke the internal delegate with an explicit string input.
     * @param input String input
     * @param context SK context
     * @param settings LLM completion settings
     * @param log Application logger
     * @returns The updated context, potentially a new one if context switching is implemented.
     */
    invokeWithInput(
        input: string,
        context?: SKContext,
        settings?: ICompleteRequestSettings,
        log?: ILogger
    ): Promise<SKContext>;

    /**
     * Set the default functions registry to use when the function is invoked without a context
     * or with a context that doesn't have a registry.
     * @param registry Kernel functions registry
     * @returns Self instance
     */
    setDefaultFunctionRegistry(registry: IFunctionRegistryReader): this;

    /**
     * Set the AI backend used by the semantic function, passing a factory method.
     * @remarks
     * The factory allows to lazily instantiate the client and to properly handle its disposal.
     * @param backendFactory AI backend factory
     * @returns Self instance
     */
    setAIBackend(backendFactory: () => ITextCompletionClient): this;

    /**
     * Set the AI completion settings used with LLM requests
     * @param settings LLM completion settings
     * @returns Self instance
     */
    setAIConfiguration(settings: ICompleteRequestSettings): this;
}

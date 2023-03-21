/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { CompleteRequestSettings, ICompleteRequestSettings, ITextCompletionClient } from '../ai';
import { Verify } from '../diagnostics';
import { ILogger, NullLogger } from '../utils/logger';
import { FunctionRegistry, IFunctionRegistryReader, IFunctionView, ISKMethodInfo, ParameterView } from '../registry';
import { ISemanticFunctionConfig } from '../semanticFunctions';
import { ContextVariables } from './contextVariables';
import { ISKFunction } from './iSKFunction';
import { SKContext } from './skContext';

export interface ISKFunctionConfig {
    /**
     * The delegate function
     */
    delegateFunction: Function;

    /**
     *  The parameters for the function
     */
    parameters: ParameterView[];

    /**
     * The name of the skill
     */
    skillName: string;

    /**
     * The name of the function
     */
    functionName: string;

    /**
     * The description of the function
     */
    description: string;

    /**
     * Whether the function is semantic or not
     */
    isSemantic?: boolean;

    /**
     * The logger
     */
    log?: ILogger;
}

export type SKNativeFunctionSignature = (
    input: string,
    context: SKContext
) => void | string | SKContext | Promise<void | string | SKContext>;
export type SKSemanticFunctionSignature = (
    client: ITextCompletionClient,
    requestSettings: ICompleteRequestSettings,
    executionContext: SKContext
) => Promise<SKContext>;

/**
 * Standard Semantic Kernel callable function.
 * SKFunction is used to extend one TypeScript <see cref="Delegate"/>, <see cref="Func{T, TResult}"/>, <see cref="Action"/>,
 * with additional methods required by the kernel.
 */
export class SKFunction implements ISKFunction {
    private _function: Function;
    private _log: ILogger;
    private _registry?: IFunctionRegistryReader;
    private _aiBackend?: ITextCompletionClient;
    private _aiRequestSettings: ICompleteRequestSettings = CompleteRequestSettings.create();

    /**
     * Constructor for SKFunction
     * @param config Function configuration info
     */
    constructor(config: ISKFunctionConfig) {
        Verify.notNull(config.delegateFunction, 'The function delegate is empty');
        Verify.validSkillName(config.skillName);
        Verify.validFunctionName(config.functionName);
        Verify.parametersUniqueness(config.parameters);

        this._log = config.log ?? new NullLogger();

        this._function = config.delegateFunction;
        this.parameters = config.parameters;

        this.isSemantic = config.isSemantic ?? true;
        this.name = config.functionName;
        this.skillName = config.skillName;
        this.description = config.description;
    }

    /**
     * @inheritdoc
     */
    public name: string;

    /**
     * @inheritdoc
     */
    public skillName: string;

    /**
     * @inheritdoc
     */
    public description: string;

    /**
     * @inheritdoc
     */
    public isSemantic: boolean;

    /**
     * @inheritdoc
     */
    public requestSettings: ICompleteRequestSettings = CompleteRequestSettings.create();

    /**
     * List of function parameters
     */
    public parameters: ParameterView[];

    /**
     * Create a native function instance, wrapping a native object method
     *
     * @param method Class method to invoke. This method should be annotated with SK decorators.
     * @param skillName SK skill name
     * @param log Application logger
     * @returns SK function instance
     */
    public static fromNativeMethod(method: ISKMethodInfo, skillName = '', log?: ILogger): ISKFunction | undefined {
        if (skillName === '') {
            skillName = FunctionRegistry.GlobalSkill;
        }

        // If the given method is not a valid SK function
        if (!method.hasSkFunctionAttribute) {
            return undefined;
        }

        return new SKFunction({
            delegateFunction: method,
            parameters: method.parameters,
            skillName: skillName,
            functionName: method.name,
            description: method.description,
            isSemantic: false,
            log: log,
        });
    }

    public static fromSemanticConfig(
        skillName: string,
        functionName: string,
        functionConfig: ISemanticFunctionConfig,
        log?: ILogger
    ): ISKFunction {
        if (!functionConfig) {
            throw new Error('Function configuration is empty');
        }

        const localFunc = async (
            client: ITextCompletionClient,
            requestSettings: ICompleteRequestSettings,
            executionContext: SKContext
        ): Promise<SKContext> => {
            if (!client) {
                throw new Error('AI LLM backed is empty');
            }

            try {
                const prompt = await functionConfig.promptTemplate.render(executionContext);

                const completion = await client.completeAsync(prompt, requestSettings);
                executionContext.variables.update(completion);
            } catch (err: any) {
                executionContext.fail((err as Error).toString());
            }

            return executionContext;
        };

        return new SKFunction({
            delegateFunction: localFunc,
            parameters: functionConfig.promptTemplate.getParameters(),
            description: functionConfig.promptTemplateConfig.description,
            skillName: skillName,
            functionName: functionName,
            isSemantic: true,
            log: log,
        });
    }

    public describe(): IFunctionView {
        return {
            isSemantic: this.isSemantic,
            name: this.name,
            skillName: this.skillName,
            description: this.description,
            parameters: this.parameters,
            isAsync: true,
        };
    }

    public invokeWithInput(
        input: string,
        context?: SKContext,
        settings?: ICompleteRequestSettings,
        log?: ILogger
    ): Promise<SKContext> {
        if (!context) {
            log = log ?? new NullLogger();
            context = new SKContext(new ContextVariables(''), this._registry, log);
        }

        context.variables.update(input);

        return this.isSemantic ? this.invokeSemantic(context, settings) : this.invokeNative(context);
    }

    public invoke(context?: SKContext, settings?: ICompleteRequestSettings, log?: ILogger): Promise<SKContext> {
        if (!context) {
            log = log ?? new NullLogger();
            context = new SKContext(new ContextVariables(''), null, log);
        }

        return this.isSemantic ? this.invokeSemantic(context, settings) : this.invokeNative(context);
    }

    /**
     * Set the default function registry
     * @param registry The registry to set
     */
    public setDefaultFunctionRegistry(registry: IFunctionRegistryReader): this {
        this._registry = registry;
        return this;
    }

    /**
     * Set the AI backend
     * @param backendFactory The factory for the AI backend
     */
    public setAIBackend(backendFactory: () => ITextCompletionClient): this {
        Verify.notNull(backendFactory, 'AI LLM backed factory is empty');
        this.verifyIsSemantic();
        this._aiBackend = backendFactory();
        return this;
    }

    /**
     * Set the AI configuration
     * @param settings The settings for the AI
     */
    public setAIConfiguration(settings: ICompleteRequestSettings): this {
        Verify.notNull(settings, 'AI LLM request settings are empty');
        this.verifyIsSemantic();
        this._aiRequestSettings = settings;
        return this;
    }

    /**
     * Dispose of the SKFunction
     */
    public dispose(): void {
        this.releaseUnmanagedResources();
    }

    /**
     * Release the unmanaged resources
     */
    private releaseUnmanagedResources(): void {
        if (typeof this._aiBackend?.dispose == 'function') {
            this._aiBackend.dispose();
        }
    }

    /**
     * Throw an exception if the function is not semantic, use this method when some logic makes sense only for semantic functions.
     * @throws Error
     */
    private verifyIsSemantic(): void {
        if (this.isSemantic) {
            return;
        }

        this._log.error('The function is not semantic');
        throw new Error('Invalid operation, the method requires a semantic function');
    }

    // Run the semantic function
    private async invokeSemantic(context: SKContext, settings?: ICompleteRequestSettings): Promise<SKContext> {
        this.verifyIsSemantic();

        this.ensureContextHasRegistry(context);

        settings = settings ?? this._aiRequestSettings;

        const callable = this._function as SKSemanticFunctionSignature;
        context.variables.update((await callable(this._aiBackend, settings, context)).variables);
        return context;
    }

    // Run the native function
    private async invokeNative(context: SKContext): Promise<SKContext> {
        this.ensureContextHasRegistry(context);

        const input = context.variables.input;
        const callable = this._function as SKNativeFunctionSignature;
        const result = await callable(input, context);
        if (typeof result == 'string') {
            context.variables.update(result);
            return context;
        } else if (typeof result == 'object' && result.variables) {
            return result;
        }

        return context;
    }

    private ensureContextHasRegistry(context: SKContext): void {
        // If the function is invoked manually, the user might have left out the registry
        if (!context.registry) {
            context.registry = this._registry;
        }
    }
}

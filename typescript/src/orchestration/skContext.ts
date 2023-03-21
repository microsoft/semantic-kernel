/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { ContextVariables } from './contextVariables';
import { IFunctionRegistryReader } from '../registry';
import { ISKFunction } from './iSKFunction';
import { Verify } from '../diagnostics';
import { ILogger, NullLogger } from '../utils/logger';

export class SKContext {
    private readonly _variables: ContextVariables;
    private readonly _log: ILogger;
    private _registry: IFunctionRegistryReader | undefined;
    private _errorOccurred: boolean = false;
    private _lastErrorDescription: string = '';
    private _lastException?: Error = undefined;

    public constructor(variables: ContextVariables, registry: IFunctionRegistryReader | undefined, logger: ILogger) {
        this._variables = variables;
        this._log = logger;
        this._registry = registry;
    }

    /**
     * Print the processed input.
     * @remarks
     * aka the current data after any processing occurred.
     */
    public get result(): string {
        return this._variables.toString();
    }

    /**
     * Whether an error occurred while executing functions in the pipeline.
     */
    public get errorOccurred(): boolean {
        return this._errorOccurred;
    }

    /**
     * Error details.
     */
    public get lastErrorDescription(): string {
        return this._lastErrorDescription;
    }

    /**
     * When an error occurs, this is the most recent exception.
     */
    public get lastException(): Error | undefined {
        return this._lastException;
    }

    /**
     * User variables
     */
    public get variables(): ContextVariables {
        return this._variables;
    }

    /**
     * Functions registry
     */
    public get registry(): IFunctionRegistryReader | undefined {
        return this._registry;
    }

    public set registry(value: IFunctionRegistryReader) {
        this._registry = value;
    }

    /**
     * App logger
     */
    public get log(): ILogger {
        return this._log;
    }

    /**
     * Call this method to signal when an error occurs.
     * @remarks
     * In the usual scenarios this is also how execution is stopped, e.g. to inform the user or take necessary steps.
     * @param errorDescription Error description
     * @param exception If available, the exception occurred
     * @returns The current instance
     */
    public fail(errorDescription: string, exception?: Error): this {
        this._errorOccurred = true;
        this._lastErrorDescription = errorDescription;
        this._lastException = exception;
        return this;
    }

    /**
     * Access registered functions by skill + name.
     * @remarks
     * Not case sensitive.
     * The function might be native or semantic, it's up to the caller handling it.
     * @param skillName Skill name
     * @param functionName Function name
     * @remarks Delegate to execute the function
     */
    public func(skillName: string, functionName: string): ISKFunction {
        Verify.notNull(this.registry, "The functions registry hasn't been set");

        if (this.registry?.hasNativeFunction(skillName, functionName)) {
            return this.registry?.getNativeFunction(skillName, functionName);
        }

        return this.registry.getSemanticFunction(skillName, functionName);
    }

    /**
     * Print the processed input, aka the current data after any processing occurred.
     * @remarks
     * If an error occurred, prints the last exception message instead.
     */
    public toString(): string {
        return this.errorOccurred ? `Error: ${this.lastErrorDescription}` : this.result;
    }

    /**
     *  Create a context from a given memory or an input string
     * @param memoryOrInput ContextVariables or input string to initialize context with.
     * @param logger Optional. Logger to use.
     * @returns Context object.
     */
    public static create(memoryOrInput: ContextVariables | string, logger?: ILogger): SKContext {
        const variables = typeof memoryOrInput == 'string' ? new ContextVariables(memoryOrInput) : memoryOrInput;
        return new SKContext(variables, undefined, logger ?? new NullLogger());
    }
}

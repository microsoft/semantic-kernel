/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { IFunctionRegistryReader } from './iFunctionRegistryReader';
import { IFunctionRegistry } from './iFunctionRegistry';
import { ISKFunction } from '../orchestration';
import { FunctionsView } from './functionsView';

/**
 * @private
 * Access the registry in read-only mode, e.g. allow templates to search and execute functions.
 */
export class FunctionRegistryReader implements IFunctionRegistryReader {
    private readonly _functionRegistry: IFunctionRegistry;

    constructor(functionRegistry: IFunctionRegistry) {
        this._functionRegistry = functionRegistry;
    }

    public hasFunction(functionName: string): boolean;
    public hasFunction(skillName: string, functionName: string): boolean;
    public hasFunction(skillOrFunctionName: string, functionName?: string): boolean {
        return this._functionRegistry.hasFunction(skillOrFunctionName, functionName);
    }

    public hasSemanticFunction(skillName: string, functionName: string): boolean {
        return this._functionRegistry.hasSemanticFunction(skillName, functionName);
    }

    public hasNativeFunction(functionName: string): boolean;
    public hasNativeFunction(skillName: string, functionName: string): boolean;
    public hasNativeFunction(skillOrFunctionName: string, functionName?: string): boolean {
        return this._functionRegistry.hasNativeFunction(skillOrFunctionName, functionName);
    }

    public getSemanticFunction(skillName: string, functionName: string): ISKFunction {
        return this._functionRegistry.getSemanticFunction(skillName, functionName);
    }

    public getNativeFunction(functionName: string): ISKFunction;
    public getNativeFunction(skillName: string, functionName: string): ISKFunction;
    public getNativeFunction(skillOrFunctionName: string, functionName?: string): ISKFunction {
        return this._functionRegistry.getNativeFunction(skillOrFunctionName, functionName);
    }

    public getFunctionsView(includeSemantic: boolean = true, includeNative: boolean = true): FunctionsView {
        return this._functionRegistry.getFunctionsView(includeSemantic, includeNative);
    }
}

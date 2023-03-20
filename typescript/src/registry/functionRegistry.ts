/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { IFunctionRegistry } from './iFunctionRegistry';
import { IFunctionRegistryReader } from './iFunctionRegistryReader';
import { ILogger, NullLogger } from '../utils/logger';
import { ISKFunction } from '../orchestration';
import { CaseInsensitiveMap } from '../utils';
import { Verify } from '../diagnostics';
import { FunctionsView } from './functionsView';
import { FunctionRegistryReader } from './functionRegistryReader';

/**
 * @private
 */
export class FunctionRegistry implements IFunctionRegistry {
    public static readonly GlobalSkill = '_GLOBAL_FUNCTIONS_';

    public readonly functionRegistryReader: IFunctionRegistryReader;

    private readonly _functionsRegistry: CaseInsensitiveMap<string, CaseInsensitiveMap<string, ISKFunction>>;
    private readonly _log: ILogger;

    constructor(log?: ILogger) {
        if (log) {
            this._log = log;
        } else {
            this._log = new NullLogger();
        }

        this.functionRegistryReader = new FunctionRegistryReader(this);

        // Important: names are case insensitive
        this._functionsRegistry = new CaseInsensitiveMap();
    }

    public registerSemanticFunction(fn: ISKFunction): this {
        Verify.notNull(fn, `The function is NULL`);
        if (!this._functionsRegistry.has(fn.skillName)) {
            // Important: names are case insensitive
            this._functionsRegistry.set(fn.skillName, new CaseInsensitiveMap());
        }

        this._functionsRegistry.get(fn.skillName)!.set(fn.name, fn);
        return this;
    }

    public registerNativeFunction(fn: ISKFunction): this {
        Verify.notNull(fn, `The function is NULL`);
        if (!this._functionsRegistry.has(fn.skillName)) {
            // Important: names are case insensitive
            this._functionsRegistry.set(fn.skillName, new CaseInsensitiveMap());
        }

        this._functionsRegistry.get(fn.skillName)!.set(fn.name, fn);
        return this;
    }

    public hasFunction(functionName: string): boolean;
    public hasFunction(skillName: string, functionName: string): boolean;
    public hasFunction(functionOrSkillName: string, functionName?: string): boolean {
        if (functionName == undefined) {
            functionName = functionOrSkillName;
            functionOrSkillName = FunctionRegistry.GlobalSkill;
        }

        return (
            this._functionsRegistry.has(functionOrSkillName) &&
            this._functionsRegistry.get(functionOrSkillName)!.has(functionName)
        );
    }

    public hasSemanticFunction(skillName: string, functionName: string): boolean {
        return (
            this.hasFunction(skillName, functionName) &&
            this._functionsRegistry.get(skillName)!.get(functionName)!.isSemantic
        );
    }

    public hasNativeFunction(functionName: string): boolean;
    public hasNativeFunction(skillName: string, functionName: string): boolean;
    public hasNativeFunction(functionOrSkillName: string, functionName?: string): boolean {
        if (functionName == undefined) {
            return this.hasNativeFunction(FunctionRegistry.GlobalSkill, functionOrSkillName);
        }

        return (
            this.hasFunction(functionOrSkillName, functionName) &&
            !this._functionsRegistry.get(functionOrSkillName)!.get(functionName)!.isSemantic
        );
    }

    public getSemanticFunction(skillName: string, functionName: string): ISKFunction {
        if (this.hasSemanticFunction(skillName, functionName)) {
            return this._functionsRegistry.get(skillName)!.get(functionName)!;
        }

        this._log.error(`Function not available: skill:${skillName} function:${functionName}`);
        throw new Error(`Function not available ${skillName}.${functionName}`);
    }

    public getNativeFunction(functionName: string): ISKFunction;
    public getNativeFunction(skillName: string, functionName: string): ISKFunction;
    public getNativeFunction(functionOrSkillName: string, functionName?: string): ISKFunction {
        if (functionName == undefined) {
            return this.getNativeFunction(FunctionRegistry.GlobalSkill, functionOrSkillName);
        }

        if (this.hasNativeFunction(functionOrSkillName, functionName)) {
            return this._functionsRegistry.get(functionOrSkillName)!.get(functionName)!;
        }

        this._log.error(`Function not available: skill:${functionOrSkillName} function:${functionName}`);
        throw new Error(`Function not available ${functionOrSkillName}.${functionName}`);
    }

    public getFunctionsView(includeSemantic: boolean = true, includeNative: boolean = true): FunctionsView {
        const result = new FunctionsView();

        if (includeSemantic) {
            for (const skill in this._functionsRegistry.keys) {
                for (const f in this._functionsRegistry.get(skill)!.keys) {
                    if (this._functionsRegistry.get(skill)!.get(f)!.isSemantic) {
                        result.addFunction(this._functionsRegistry!.get(skill)!.get(f)!.describe());
                    }
                }
            }
        }

        if (!includeNative) {
            return result;
        }

        for (const skill in this._functionsRegistry.keys) {
            for (const f in this._functionsRegistry.get(skill)!.keys) {
                if (!this._functionsRegistry.get(skill)!.get(f)!.isSemantic) {
                    result.addFunction(this._functionsRegistry.get(skill)!.get(f)!.describe());
                }
            }
        }

        return result;
    }
}

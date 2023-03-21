/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { KernelConfig } from './configuration';
import { CaseInsensitiveMap } from './utils';
import { ILogger } from './utils/logger';
import { ContextVariables, ISKFunction, SKContext } from './orchestration';
import { IFunctionRegistryReader } from './registry';
import { ISemanticFunctionConfig } from './semanticFunctions';
import { IPromptTemplateEngine } from './templateEngine';

export interface IKernel {
    /**
     * Settings required to execute functions, including details about AI dependencies, e.g. endpoints and API keys.
     */
    config: KernelConfig;

    /**
     * App logger
     */
    log: ILogger;

    /**
     * Reference to the engine rendering prompt templates
     */
    promptTemplateEngine: IPromptTemplateEngine;

    /**
     * Reference to the read-only registry containing all the imported functions
     */
    functionRegistryReader: IFunctionRegistryReader;

    /**
     * Build and register a function in the internal registry, in a global generic skill.
     * @param functionName Name of the semantic function. The name can contain only alphanumeric chars + underscore.
     * @param functionConfig Function configuration, e.g. I/O params, AI settings, localization details, etc.
     * @returns A C# function wrapping AI logic, usually defined with natural language
     */
    registerSemanticFunction(functionName: string, functionConfig: ISemanticFunctionConfig): ISKFunction;

    /**
     * Build and register a function in the internal registry.
     * @param skillName Name of the skill containing the function. The name can contain only alphanumeric chars + underscore.
     * @param functionName Name of the semantic function. The name can contain only alphanumeric chars + underscore.
     * @param functionConfig Function configuration, e.g. I/O params, AI settings, localization details, etc.
     * @returns A C# function wrapping AI logic, usually defined with natural language
     */
    registerSemanticFunction(
        skillName: string,
        functionName: string,
        functionConfig: ISemanticFunctionConfig
    ): ISKFunction;

    /**
     * Import a set of functions from the given skill. The functions must have the `SKFunction` attribute.
     * Once these functions are imported, the prompt templates can use functions to import content at runtime.
     * @param skillInstance Instance of a class containing functions
     * @param skillName Name of the skill for registry and prompt templates. If the value is empty functions are registered in the global namespace.
     * @returns A list of all the semantic functions found in the directory, indexed by function name.
     */
    importSkill(skillInstance: any, skillName?: string): CaseInsensitiveMap<string, ISKFunction>;

    /**
     * Run a pipeline composed by synchronous and asynchronous functions.
     * @param variables Input to process
     * @param pipeline List of functions
     * @returns Result of the function composition
     */
    run(variables: ContextVariables, ...pipeline: ISKFunction[]): Promise<SKContext>;

    /**
     * Access registered functions by skill + name. Not case sensitive.
     * The function might be native or semantic, it's up to the caller handling it.
     * @param skillName Skill name
     * @param functionName Function name
     * @returns Delegate to execute the function
     */
    func(skillName: string, functionName: string): ISKFunction;
}

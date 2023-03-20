// Copyright (c) Microsoft Corporation. All rights reserved.

import { KernelConfig } from './configuration/kernelConfig';
import { ISemanticTextMemory } from './memory/iSemanticTextMemory';
import { ContextVariables, ISKFunction, SKContext } from './orchestration';
import { SemanticFunctionConfig } from './semanticFunctions/semanticFunctionConfig';
import { IReadOnlySkillCollection } from './skillDefinition';
import { IPromptTemplateEngine } from './templateEngine/iPromptTemplateEngine';
import { ILogger } from './utils/logger';

export interface IKernel {
    // Settings required to execute functions, including details about AI dependencies, e.g. endpoints and API keys.
    readonly config: KernelConfig;

    // Application logger.
    readonly log: ILogger;

    // Semantic memory instance.
    readonly memory: ISemanticTextMemory;

    // Reference to the engine rendering prompt templates.
    readonly promptTemplateEngine: IPromptTemplateEngine;

    // Reference to the read-only skill collection containing all the imported functions.
    readonly skills: IReadOnlySkillCollection;

    /**
     * Build and register a function in the internal skill collection, in a global generic skill.
     *
     * @param functionName Name of the semantic function. The name can contain only alphanumeric chars + underscore.
     * @param functionConfig Function configuration, e.g. I/O params, AI settings, localization details, etc.
     * @returns A AI logic wrapper, usually defined with natural language
     */
    registerSemanticFunction(functionName: string, functionConfig: SemanticFunctionConfig): ISKFunction;

    /**
     * Build and register a function in the internal skill collection.
     *
     * @param skllName Name of the skill containing the function. The name can contain only alphanumeric chars + underscore.
     * @param functionName Name of the semantic function. The name can contain only alphanumeric chars + underscore.
     * @param functionConfig Function configuration, e.g. I/O params, AI settings, localization details, etc.
     * @returns A AI logic wrapper, usually defined with natural language
     */
    registerSemanticFunction(
        skillName: string,
        functionName: string,
        functionConfig: SemanticFunctionConfig
    ): ISKFunction;

    /**
     * Import a set of functions from the given skill. The functions must have the `SKFunction` attribute.
     * Once these functions are imported, the prompt templates can use functions to import content at runtime.
     *
     * @param skillInstance Instance of a class containing functions.
     * @param skillName Name of the skill for skill collection and prompt templates. If the value is empty functions are registered in the global namespace.
     * @returns A list of all the semantic functions found in the directory, indexed by function name.
     */
    importSkill(skillInstance: any, skillName?: string): Map<string, ISKFunction>;

    /**
     * Set the semantic memory to use.
     *
     * @param memory Semantic memory instance.
     */
    registerMemory(memory: ISemanticTextMemory): void;

    /**
     * Run a pipeline composed of synchronous and asynchronous functions.
     *
     * @param pipeline List of functions.
     * @returns Result of the function composition.
     */
    run(pipeline: ISKFunction[]): Promise<SKContext>;

    /**
     * Run a pipeline composed of synchronous and asynchronous functions.
     *
     * @param input Input to process.
     * @param pipeline List of functions.
     * @returns Result of the function composition.
     */
    run(input: string, pipeline: ISKFunction[]): Promise<SKContext>;

    /**
     * Run a pipeline composed of synchronous and asynchronous functions.
     *
     * @param variables Input to process.
     * @param pipeline List of functions.
     * @returns Result of the function composition.
     */
    run(variables: ContextVariables, pipeline: ISKFunction[]): Promise<SKContext>;

    /**
     * Access registered functions by skill + name. Not case sensitive.
     * The function might be native or semantic, it's up to the caller handling it.
     *
     * @param skillName Skill name.
     * @param functionName Function name.
     * @returns Delegate to execute the function.
     */
    func(skillName: string, functionName: string): ISKFunction;

    /**
     * Create a new instance of a context, linked to the kernel internal state.
     */
    createNewContext(): SKContext;
}

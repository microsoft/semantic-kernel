// Copyright (c) Microsoft. All rights reserved.

import { ISKFunction } from '../orchestration/iSKFunction';
import { FunctionsView } from './functionsView';

/**
 * Read-only skill collection interface.
 */
export interface IReadOnlySkillCollection {
    /**
     * Check if the collection contains the specified function in the global skill,
     * regardless of the function type.
     *
     * @param functionName Function name.
     * @returns True if the function exists, false otherwise.
     */
    hasFunction(functionName: string): boolean;

    /**
     * Check if a native function is registered in global skill.
     *
     * @param functionName Function name.
     * @returns True if the function exists, false otherwise.
     */
    hasNativeFunction(functionName: string): boolean;

    /**
     * Check if a semantic function is registered.
     *
     * @param skillName Skill name.
     * @param functionName Function name.
     * @returns True if the function exists, false otherwise.
     */
    hasSkillFunction(skillName: string, functionName: string): boolean;

    /**
     * Check if the collection contains the specified function, regardless of the function type.
     *
     * @param skillName Skill name.
     * @param functionName Function name.
     * @returns True if the function exists, false otherwise.
     */
    hasSemanticSkillFunction(skillName: string, functionName: string): boolean;

    /**
     * Check if a native function is registered.
     *
     * @param skillName Skill name.
     * @param functionName Function name.
     * @returns True if the function exists, false otherwise.
     */
    hasNativeSkillFunction(skillName: string, functionName: string): boolean;

    /**
     * Return the function delegate stored in the global collection, regardless of the function type.
     *
     * @param functionName Skill name.
     * @returns Semantic function delegate.
     */
    getFunction(functionName: string): ISKFunction;

    /**
     * Return the function delegate stored in the collection, regardless of the function type.
     *
     * @param skillName Function name.
     * @param functionName Skill name.
     * @returns Semantic function delegate.
     */
    getSkillFunction(skillName: string, functionName: string): ISKFunction;

    /**
     * Return the semantic function delegate stored in the global collection.
     *
     * @param functionName Skill name.
     * @returns Semantic function delegate.
     */
    getSemanticFunction(functionName: string): ISKFunction;

    /**
     * Return the semantic function delegate stored in the collection.
     *
     * @param skillName Function name.
     * @param functionName Skill name.
     * @returns Semantic function delegate.
     */
    getSemanticSkillFunction(skillName: string, functionName: string): ISKFunction;

    /**
     * Return the native function delegate stored in the global collection.
     *
     * @param functionName Skill name.
     * @returns Native function delegate.
     */
    getNativeFunction(functionName: string): ISKFunction;

    /**
     * Return the native function delegate stored in the collection.
     *
     * @param skillName Function name.
     * @param functionName Skill name.
     * @returns Native function delegate.
     */
    getNativeSkillFunction(skillName: string, functionName: string): ISKFunction;

    /**
     * Get all registered functions details, minus the delegates.
     *
     * @param includeSemantic Whether to include semantic functions in the list.
     * @param includeNative Whether to include native functions in the list.
     * @returns An object containing all the functions details
     */
    getFunctionsView(includeSemantic: boolean, includeNative: boolean): FunctionsView;
}

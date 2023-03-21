/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { ISKFunction } from '../orchestration';
import { FunctionsView } from './functionsView';

export interface IFunctionRegistryReader {
    /**
     * Check if the registry contains the specified function in the global skill, regardless of the function type
     * @param skillName Skill name
     * @param functionName Function name
     * @returns True if the function exists, false otherwise
     */
    hasFunction(skillName: string, functionName: string): boolean;

    /**
     * Check if the registry contains the specified function, regardless of the function type
     * @param functionName Function name
     * @returns True if the function exists, false otherwise
     */
    hasFunction(functionName: string): boolean;

    /**
     * Check if a semantic function is registered
     * @param functionName Function name
     * @param skillName Skill name
     * @returns True if the function exists
     */
    hasSemanticFunction(skillName: string, functionName: string): boolean;

    /**
     * Check if a native function is registered
     * @param functionName Function name
     * @param skillName Skill name
     * @returns True if the function exists
     */
    hasNativeFunction(skillName: string, functionName: string): boolean;

    /**
     * Check if a native function is registered in the global skill
     * @param functionName Function name
     * @returns True if the function exists
     */
    hasNativeFunction(functionName: string): boolean;

    /**
     * Return the semantic function delegate stored in the registry
     * @param functionName Function name
     * @param skillName Skill name
     * @returns Semantic function delegate
     */
    getSemanticFunction(skillName: string, functionName: string): ISKFunction;

    /**
     * Return the native function delegate stored in the registry
     * @param functionName Function name
     * @param skillName Skill name
     * @returns Native function delegate
     */
    getNativeFunction(skillName: string, functionName: string): ISKFunction;

    /**
     * Return the native function delegate stored in the registry
     * @param functionName Function name
     * @returns Native function delegate
     */
    getNativeFunction(functionName: string): ISKFunction;

    /**
     * Get all registered functions details, minus the delegates
     * @param includeSemantic Whether to include semantic functions in the list
     * @param includeNative Whether to include native functions in the list
     * @returns An object containing all the functions details
     */
    getFunctionsView(includeSemantic?: boolean, includeNative?: boolean): FunctionsView;
}

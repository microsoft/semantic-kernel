/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { CaseInsensitiveMap } from '../utils';
import { IFunctionView } from './functionView';

/**
 * Class used to copy and export data from the registry.
 * The data is mutable, but changes do not affect the registry.
 * The class can be used to create custom lists in case your scenario needs to.
 */
export class FunctionsView {
    /**
     * Collection of semantic skill names and function names, including function parameters.
     * @remarks
     * Functions are grouped by skill name.
     */
    public readonly semanticFunctions: CaseInsensitiveMap<string, IFunctionView[]> = new CaseInsensitiveMap();

    /**
     * Collection of native skill names and function views, including function parameters.
     * @remarks
     * Functions are grouped by skill name.
     */
    public readonly nativeFunctions: CaseInsensitiveMap<string, IFunctionView[]> = new CaseInsensitiveMap();

    /**
     * Add a function to the list
     * @param view Function details
     * @returns Current instance
     */
    public addFunction(view: IFunctionView): FunctionsView {
        if (view.isSemantic) {
            if (!this.semanticFunctions.has(view.skillName)) {
                this.semanticFunctions.set(view.skillName, []);
            }

            this.semanticFunctions.get(view.skillName)!.push(view);
        } else {
            if (!this.nativeFunctions.has(view.skillName)) {
                this.nativeFunctions.set(view.skillName, []);
            }

            this.nativeFunctions.get(view.skillName)!.push(view);
        }

        return this;
    }

    /**
     * Returns true if the function specified is unique and semantic
     * @param skillName Skill name
     * @param functionName Function name
     * @returns True if unique and semantic
     */
    public isSemantic(skillName: string, functionName: string): boolean {
        const fnName = functionName.toLowerCase();
        const sf =
            this.semanticFunctions.has(skillName) &&
            this.semanticFunctions.get(skillName)!.filter((x) => x.name.toLowerCase() == fnName).length > 0;

        const nf =
            this.nativeFunctions.has(skillName) &&
            this.nativeFunctions.get(skillName)!.filter((x) => x.name.toLowerCase() === fnName).length > 0;

        if (sf && nf) {
            throw new Error('There are 2 functions with the same name, one native and one semantic');
        }

        return sf;
    }

    /**
     * Returns true if the function specified is unique and native
     * @param skillName Skill name
     * @param functionName Function name
     * @returns True if unique and native
     */
    public isNative(skillName: string, functionName: string): boolean {
        const fnName = functionName.toLowerCase();
        const sf =
            this.semanticFunctions.has(skillName) &&
            this.semanticFunctions.get(skillName)!.filter((x) => x.name.toLowerCase() == fnName).length > 0;

        const nf =
            this.nativeFunctions.has(skillName) &&
            this.nativeFunctions.get(skillName)!.filter((x) => x.name.toLowerCase() === fnName).length > 0;

        if (sf && nf) {
            throw new Error('There are 2 functions with the same name, one native and one semantic');
        }

        return nf;
    }
}

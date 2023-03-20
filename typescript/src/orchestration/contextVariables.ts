/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { CaseInsensitiveMap } from '../utils';
import { Verify } from '../diagnostics';

export class ContextVariables {
    private readonly MainKey = 'INPUT';

    // Important: names are case insensitive
    private readonly _variables: CaseInsensitiveMap<string, string> = new CaseInsensitiveMap();

    public constructor(content: string = '') {
        this._variables.set(this.MainKey, content);
        this.input = content;
    }

    /**
     * In the simplest scenario, the data is an input string, stored here.
     */
    public input: string;

    /**
     * Updates the main input text with the new value after a function is complete.
     * @param content he new input value, for the next function in the pipeline, or
     * as a result for the user if the pipeline reached the end.
     * @returns The current instance
     */
    public update(content: string): this;

    /**
     * Updates all the local data with new data, merging the two datasets.
     * @remarks
     * Does not discard old data
     * @param newData New data to be merged
     * @param merge Whether to merge and keep old data, or replace. False == discard old data.
     * @returns The current instance
     */
    public update(newData: ContextVariables, merge?: boolean): this;

    public update(newData: string | ContextVariables, merge = true): this {
        if (typeof newData == 'string') {
            this._variables.set(this.MainKey, newData);
        } else {
            // If requested, discard old data and keep only the new one.
            if (!merge) {
                this._variables.clear();
            }

            newData._variables.forEach((value, key) => {
                this._variables.set(key, value);
            });
        }

        return this;
    }

    /**
     * This method allows to store additional data in the context variables.
     * @remarks
     * e.g. variables needed by functions in the pipeline. These "variables" are visible
     * also to semantic functions using the "{{varName}}" syntax, allowing to inject more
     * information into prompt templates.
     * @param name Variable name
     * @param value Value to store. If the value is NULL the variable is deleted.
     */
    public set(name: string, value?: string): void {
        // TODO: support for more complex data types, and plan for rendering these values into prompt templates.
        Verify.notEmpty(name, `The variable name is empty`);
        if (value) {
            this._variables.set(name, value);
        } else {
            this._variables.delete(name);
        }
    }

    /**
     * Fetch a variable value from the context variables.
     * @param name Variable name
     * @returns The string value or undefined if missing.
     */
    public get(name: string): string | undefined {
        return this._variables.get(name);
    }

    /**
     * Returns true if there is a variable with the given name
     * @param name Variable name
     * @returns True if there is a variable with the given name, false otherwise
     */
    public has(name: string): boolean {
        return this._variables.has(name);
    }

    /**
     * Print the processed input.
     * @remarks
     * aka the current data after any processing occurred.
     */
    public toString(): string {
        return this.input;
    }
}

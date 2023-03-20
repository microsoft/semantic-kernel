/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { ILogger } from '../../utils/logger';
import { ContextVariables, ISKFunction, SKContext, SKFunctionExtensions } from '../../orchestration';
import { IFunctionRegistryReader } from '../../registry';
import { Block, BlockTypes } from './block';
import { VarBlock } from './varBlock';

/**
 * @private
 */
export class CodeBlock extends Block {
    private _validated: boolean = false;

    constructor(public content: string, log: ILogger) {
        super(log);
    }

    public get type(): BlockTypes {
        return BlockTypes.Code;
    }

    public isValid(): { valid: boolean; error: string } {
        let valid = true;
        let error = '';

        const partsToValidate = this.content.split(/[ \t\r\n]+/).filter((x) => x.trim() !== '');

        for (let index = 0; index < partsToValidate.length; index++) {
            const part = partsToValidate[index];

            if (index === 0) {
                // There is only a function name
                if (VarBlock.hasVarPrefix(part)) {
                    error = `Variables cannot be used as function names [\`${part}\`]`;
                    this.log.error(error);
                    valid = false;
                }

                if (!/^[a-zA-Z0-9_.]*$/.test(part)) {
                    error = `The function name \`${part}\` contains invalid characters`;
                    this.log.error(error);
                    valid = false;
                }
            } else {
                // The function has parameters
                if (!VarBlock.hasVarPrefix(part)) {
                    error = `\`${part}\` is not a valid function parameter: parameters must be variables.`;
                    this.log.error(error);
                    valid = false;
                }

                if (part.length < 2) {
                    error = `\`${part}\` is not a valid variable.`;
                    this.log.error(error);
                    valid = false;
                }

                if (!VarBlock.isValidVarName(part.substring(1))) {
                    error = `\`${part}\` variable name is not valid.`;
                    this.log.error(error);
                    valid = false;
                }
            }
        }

        this._validated = true;

        return { valid, error };
    }

    public render(variables?: ContextVariables): string {
        throw new Error('Code blocks rendering requires IFunctionRegistryReader. Incorrect method call.');
    }

    public async renderCode(context: SKContext): Promise<string> {
        if (!this._validated) {
            const { valid, error } = this.isValid();
            if (!valid) {
                throw new Error(error);
            }
        }

        this.log.trace(`Rendering code: "${this.content}"`);

        const parts = this.content.split(/[ \t\r\n]+/).filter((x) => x.trim() !== '');

        const functionName = parts[0];
        if (!context.registry) {
            throw new Error('Registry not set');
        }

        const fn = this.getFunctionFromRegistry(context.registry, functionName);
        if (!fn) {
            this.log.warn(`Function not found "${functionName}"`);
            return '';
        }

        // Using $input by default, e.g. when the syntax is {{functionName}}
        let funcParam = context.variables.input ?? '';
        if (parts.length > 1) {
            this.log.trace(`Passing required variable: "${parts[1]}"`);
            // If the code syntax is {{functionName $varName}} use $varName instead of $input
            funcParam = new VarBlock(parts[1], this.log).render(context.variables);
        }

        const result = await SKFunctionExtensions.invokeWithCustomInput(fn, new ContextVariables(funcParam), this.log);

        if (result.errorOccurred) {
            this.log.error(
                `Semantic function references a function "${functionName}" of incompatible type: defaulting to an empty result`
            );
            return '';
        }

        return result.result;
    }

    private getFunctionFromRegistry(registry: IFunctionRegistryReader, functionName: string): ISKFunction | undefined {
        // Search in the global space (only native functions there)
        if (registry.hasNativeFunction(functionName)) {
            return registry.getNativeFunction(functionName);
        }

        // If the function contains a skill name...
        if (functionName.includes('.')) {
            const functionNameParts = functionName.split('.');
            if (functionNameParts.length > 2) {
                this.log.error(`Invalid function name "${functionName}"`);
                throw new Error(
                    `Invalid function name "${functionName}". ` +
                        `A Function name can contain only one "." to separate skill name from function name.`
                );
            }

            const skillName = functionNameParts[0];
            functionName = functionNameParts[1];

            if (registry.hasNativeFunction(skillName, functionName)) {
                return registry.getNativeFunction(skillName, functionName);
            }

            if (registry.hasSemanticFunction(skillName, functionName)) {
                return registry.getSemanticFunction(skillName, functionName);
            }
        }

        return undefined;
    }
}

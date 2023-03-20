/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { ILogger } from '../../utils/logger';
import { ContextVariables } from '../../orchestration';
import { Block, BlockTypes } from './block';

/**
 * @private
 */
export class VarBlock extends Block {
    private static readonly Prefix: string = '$';

    public readonly name: string = this.varName();

    constructor(public content: string, log?: ILogger) {
        super(log);
    }

    public get type(): BlockTypes {
        return BlockTypes.Variable;
    }

    public isValid(): { valid: boolean; error: string } {
        let valid = true;
        let error = '';

        if (this.content[0] !== VarBlock.Prefix) {
            error = `A variable must start with the symbol ${VarBlock.Prefix}`;
            this.log.error(error);
            valid = false;
        } else if (this.content.length < 2) {
            error = 'The variable name is empty';
            this.log.error(error);
            valid = false;
        } else {
            const varName = this.varName();
            if (!/^[a-zA-Z0-9_]*$/.test(varName)) {
                error = `The variable name '${varName}' contains invalid characters. Only alphanumeric chars and underscore are allowed.`;
                this.log.error(error);
                valid = false;
            }
        }

        return { valid, error };
    }

    public render(workingMemory?: ContextVariables): string {
        if (!workingMemory) {
            return '';
        }

        const name = this.varName();
        if (name) {
            const value = workingMemory.get(name);
            if (value == undefined) {
                this.log.warn(`Variable \`${VarBlock.Prefix}${name}\` not found`);
            }

            return value ?? '';
        }

        this.log.error('Variable rendering failed, the variable name is empty');
        throw new Error('Variable rendering failed, the variable name is empty.');
    }

    public static hasVarPrefix(text: string): boolean {
        return !!text && text.length > 0 && text[0] === VarBlock.Prefix;
    }

    public static isValidVarName(text: string): boolean {
        return /^[a-zA-Z0-9_]*$/.test(text);
    }

    private varName(): string {
        return this.content.length < 2 ? '' : this.content.slice(1);
    }
}

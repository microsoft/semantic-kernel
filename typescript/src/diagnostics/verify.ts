/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import fs from 'fs';
import { ParameterView } from '../registry';

export class Verify {
    public static notNull(obj: any, message: string): void {
        if (obj !== null && obj !== undefined) {
            return;
        }

        throw new Error(message);
    }

    public static notEmpty(str: string, message: string): void {
        Verify.notNull(str, message);
        if (!str.trim()) {
            throw new Error(message);
        }
    }

    public static validSkillName(skillName: string): void {
        Verify.notEmpty(skillName, 'The skill name cannot be empty');
        const pattern = new RegExp('^[0-9A-Za-z_]*$');
        if (!pattern.test(skillName)) {
            throw new Error(
                `A skill name can contain only latin letters, 0-9 digits, and underscore: '${skillName}' is not a valid name.`
            );
        }
    }

    public static validFunctionName(functionName: string): void {
        Verify.notEmpty(functionName, 'The function name cannot be empty');
        const pattern = new RegExp('^[0-9A-Za-z_]*$');
        if (!pattern.test(functionName)) {
            throw new Error(
                `A function name can contain only latin letters, 0-9 digits, and underscore: '${functionName}' is not a valid name.`
            );
        }
    }

    public static validFunctionParamName(functionParamName: string): void {
        Verify.notEmpty(functionParamName, 'The function parameter name cannot be empty');
        const pattern = new RegExp('^[0-9A-Za-z_]*$');
        if (!pattern.test(functionParamName)) {
            throw new Error(
                `A function parameter name can contain only latin letters, 0-9 digits, and underscore: '${functionParamName}' is not a valid name.`
            );
        }
    }

    public static startsWith(text: string, prefix: string, message: string): void {
        Verify.notEmpty(text, 'The text to verify cannot be empty');
        Verify.notNull(prefix, 'The prefix to verify is empty');
        if (text.toLowerCase().startsWith(prefix.toLowerCase())) {
            return;
        }

        throw new Error(message);
    }

    public static directoryExists(path: string): void {
        if (fs.existsSync(path)) {
            return;
        }

        throw new Error(`Directory not found: ${path}`);
    }

    public static parametersUniqueness(parameters: ParameterView[]): void {
        const x: string[] = [];
        for (const p of parameters) {
            const key = p.name.toLowerCase();
            if (x.indexOf(key)) {
                throw new Error(`The function has two or more parameters with the same name '${p.name}'`);
            }

            Verify.notEmpty(p.name, 'The parameter name is empty');
            x.push(key);
        }
    }
}

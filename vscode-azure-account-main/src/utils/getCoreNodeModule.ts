/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See LICENSE.md in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';

/**
 * Returns a node module installed with VSCode, or undefined if it fails.
 */
export function getCoreNodeModule<T>(moduleName: string): T | undefined {
    try {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-return
        return require(`${vscode.env.appRoot}/node_modules.asar/${moduleName}`);
    } catch (err) {
        // ignore
    }

    try {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-return
        return require(`${vscode.env.appRoot}/node_modules/${moduleName}`);
    } catch (err) {
        // ignore
    }
    return undefined;
}

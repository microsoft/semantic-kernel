/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See LICENSE.md in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

"use strict";

// This is the extension entrypoint module, which imports extension.bundle.js, the actual extension code.
//
// This is in a separate file so we can properly measure extension.bundle.js load time.

let perfStats = {
    loadStartTime: Date.now(),
    loadEndTime: undefined
};

Object.defineProperty(exports, "__esModule", { value: true });

const extension = require('./dist/extension.bundle');

async function activate(ctx) {
    return await extension.activateInternal(ctx, perfStats);
}

async function deactivate(ctx) {
    return await extension.deactivateInternal(ctx, perfStats);
}

// Export as entrypoints for vscode
exports.activate = activate;
exports.deactivate = deactivate;

perfStats.loadEndTime = Date.now();

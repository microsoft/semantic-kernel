/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

//@ts-check

// See https://github.com/Microsoft/vscode-azuretools/wiki/webpack for guidance

'use strict';

const process = require('process');
const dev = require("vscode-azureextensiondev");
const CopyWebpackPlugin = require('copy-webpack-plugin');

let DEBUG_WEBPACK = !!process.env.DEBUG_WEBPACK;

let config = dev.getDefaultWebpackConfig({
	entries: {
		cloudConsoleLauncher: './src/cloudConsole/cloudConsoleLauncher.ts',
	},
    projectRoot: __dirname,
    verbosity: DEBUG_WEBPACK ? 'debug' : 'normal',
    externals: {
		bufferutil: 'commonjs bufferutil',
		'utf-8-validate': 'commonjs utf-8-validate',
		'./platform/openbsd': 'commonjs copy-paste-openbsd',
	},
    plugins: [
        new CopyWebpackPlugin({
            patterns: [
                { from: './out/src/utils/getCoreNodeModule.js', to: 'node_modules' }
            ]
        })
    ]
});

if (DEBUG_WEBPACK) {
    console.log('Config:', config);
}

module.exports = config;

/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

// this file is run as a child process from the extension host and communicates via IPC
import * as http from 'http';
import { HttpProxyAgent } from 'http-proxy-agent';
import { HttpsProxyAgent } from 'https-proxy-agent';
import * as request from 'request-promise';
import * as WS from 'ws';
import { delay } from '../utils/timeUtils';
import { readJSON, sendData } from './ipc';

export interface AccessTokens {
	resource: string;
	graph: string;
	keyVault?: string;
}

export interface ConsoleUris {
	consoleUri: string;
	terminalUri: string;
	socketUri: string;
}

export interface Size {
	cols: number;
	rows: number;
}

function getWindowSize(): Size {
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	const stdout: any = process.stdout;
	// eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
	const windowSize: [number, number] = stdout.isTTY ? stdout.getWindowSize() : [80, 30];
	return {
		cols: windowSize[0],
		rows: windowSize[1],
	};
}

let resizeToken = {};
async function resize(accessTokens: AccessTokens, terminalUri: string) {
	const token = resizeToken = {};
	await delay(300);

	for (let i = 0; i < 10; i++) {
		if (token !== resizeToken) {
			return;
		}

		const { cols, rows } = getWindowSize();
		// eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
		const response = await request({
			uri: `${terminalUri}/size?cols=${cols}&rows=${rows}`,
			method: 'POST',
			headers: {
				'Accept': 'application/json',
				'Content-Type': 'application/json',
				'Authorization': `Bearer ${accessTokens.resource}`
			},
			simple: false,
			resolveWithFullResponse: true,
			json: true,
			// Provide empty body so that 'Content-Type' header is set properly
			body: {}
		});

		/* eslint-disable @typescript-eslint/no-unsafe-member-access */
		if (response.statusCode < 200 || response.statusCode > 299) {
			if (response.statusCode !== 503 && response.statusCode !== 504 && response.body && response.body.error) {
				if (response.body && response.body.error && response.body.error.message) {
					console.log(`${response.body.error.message} (${response.statusCode})`);
				} else {
					console.log(response.statusCode, response.headers, response.body);
				}
				break;
			}
			await delay(1000 * (i + 1));
			continue;
		}
		/* eslint-enable @typescript-eslint/no-unsafe-member-access */

		return;
	}

	console.log('Failed to resize terminal.');
}

function connectSocket(ipcHandle: string, url: string) {

	const proxy = process.env.HTTPS_PROXY || process.env.HTTP_PROXY || undefined;
	let agent: http.Agent | undefined = undefined;
	if (proxy) {
		agent = url.startsWith('ws:') || url.startsWith('http:') ? new HttpProxyAgent(proxy) : new HttpsProxyAgent(proxy);
	}

	const ws = new WS(url, {
		agent
	});

	ws.on('open', function () {
		process.stdin.on('data', function (data) {
			ws.send(data);
		});
		startKeepAlive();
		sendData(ipcHandle, JSON.stringify([ { type: 'status', status: 'Connected' } ]))
			.catch(err => {
				console.error(err);
			});
	});

	ws.on('message', function (data) {
		process.stdout.write(String(data));
	});

	let error = false;
	ws.on('error', function (event) {
		error = true;
		console.error('Socket error: ' + JSON.stringify(event));
	});

	ws.on('close', function () {
		console.log('Socket closed');
		sendData(ipcHandle, JSON.stringify([ { type: 'status', status: 'Disconnected' } ]))
			.catch(err => {
				console.error(err);
			});
		if (!error) {
			process.exit(0);
		}
	});

	function startKeepAlive() {
		let isAlive = true;
		ws.on('pong', () => {
			isAlive = true;
		});
		const timer = setInterval(() => {
			if (isAlive === false) {
				error = true;
				console.log('Socket timeout');
				ws.terminate();
				clearInterval(timer);
			} else {
				isAlive = false;
				ws.ping();
			}
		}, 60000);
		timer.unref();
	}
}

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export function main() {
	// eslint-disable-next-line @typescript-eslint/no-non-null-assertion
	process.stdin.setRawMode!(true);
	process.stdin.resume();

	// eslint-disable-next-line @typescript-eslint/no-non-null-assertion
	const ipcHandle = process.env.CLOUD_CONSOLE_IPC!;
	(async () => {
		void sendData(ipcHandle, JSON.stringify([ { type: 'size', size: getWindowSize() } ]));
		let res: http.IncomingMessage;
		// eslint-disable-next-line no-cond-assign
		while (res = await sendData(ipcHandle, JSON.stringify([ { type: 'poll' } ]))) {
			// eslint-disable-next-line @typescript-eslint/no-explicit-any
			for (const message of await readJSON<any>(res)) {
				/* eslint-disable @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-assignment */
				if (message.type === 'log') {
					console.log(...message.args);
				} else if (message.type === 'connect') {
					try {
						const accessTokens: AccessTokens = message.accessTokens;
						const consoleUris: ConsoleUris = message.consoleUris;
						connectSocket(ipcHandle, consoleUris.socketUri);
						process.stdout.on('resize', () => {
							resize(accessTokens, consoleUris.terminalUri)
								.catch(console.error);
						});
					} catch(err) {
						console.error(err);
						sendData(ipcHandle, JSON.stringify([ { type: 'status', status: 'Disconnected' } ]))
							.catch(err => {
								console.error(err);
							});
					}
				} else if (message.type === 'exit') {
					process.exit(message.code);
				}
				/* eslint-enable @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-assignment */
			}
		}
	})()
		.catch(console.error);
}

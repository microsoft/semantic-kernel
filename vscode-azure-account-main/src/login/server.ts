/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { IActionContext } from '@microsoft/vscode-azext-utils';
import * as fs from 'fs';
import * as http from 'http';
import * as https from 'https';
import * as net from 'net';
import * as path from 'path';
import { parse, ParsedUrlQuery } from 'querystring';
import * as url from 'url';
import { authTimeoutMs, portADFS, redirectUrlAAD } from '../constants';
import { ext } from '../extensionVariables';
import { localize } from '../utils/localize';
import { logErrorMessage } from '../utils/logErrorMessage';
import { Deferred } from '../utils/promiseUtils';
import { getLocalCallbackUrl } from './getCallbackUrl';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type RedirectResult = { req: http.IncomingMessage, res: http.ServerResponse } | { err: any; res: http.ServerResponse; };

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type CodeResult = { code: string; res: http.ServerResponse; } | { err: any; res: http.ServerResponse; };

export async function checkRedirectServer(isAdfs: boolean): Promise<boolean> {
	if (isAdfs) {
		return true;
	}
	const testCallbackUrl: string = getLocalCallbackUrl(3333);
	let timer: NodeJS.Timer | undefined;
	const checkServerPromise = new Promise<boolean>(resolve => {
		const req: http.ClientRequest = https.get({
			...url.parse(`${redirectUrlAAD}?state=${testCallbackUrl}?nonce=cccc`),
		}, res => {
			const key: string | undefined = Object.keys(res.headers)
				.find(key => key.toLowerCase() === 'location');
			const location: string | string[] | undefined = key && res.headers[key]
			resolve(res.statusCode === 302 && typeof location === 'string' && location.startsWith(testCallbackUrl));
		});
		req.on('error', error => {
			logErrorMessage(error);
			resolve(false);
		});
		req.on('close', () => {
			resolve(false);
		});
		timer = setTimeout(() => {
			resolve(false);
			req.abort();
		}, 5000);
	});
	function cancelTimer() {
		if (timer) {
			clearTimeout(timer);
		}
	}
	checkServerPromise.then(cancelTimer, cancelTimer);
	return checkServerPromise;
}

export function createServer(context: IActionContext, nonce: string): {
    server: http.Server;
    redirectPromise: Promise<RedirectResult>;
    codePromise: Promise<CodeResult>;
	codeTimer: NodeJS.Timeout;
} {
	let deferredRedirect: Deferred<RedirectResult>;
	const redirectPromise = new Promise<RedirectResult>((resolve, reject) => deferredRedirect = { resolve, reject });

	let deferredCode: Deferred<CodeResult>;
	const codePromise = new Promise<CodeResult>((resolve, reject) => deferredCode = { resolve, reject });

	const codeTimer = setTimeout(() => {
		context.errorHandling.suppressDisplay = true;
		const message: string = localize('azure-account.timeoutWaitingForCode', 'Timeout waiting for code.');
		deferredCode.reject(new Error(message));
	}, authTimeoutMs);

	function cancelCodeTimer() {
		clearTimeout(codeTimer);
	}

	const server: http.Server = http.createServer(function (req, res) {
		// eslint-disable-next-line @typescript-eslint/no-non-null-assertion
		const reqUrl: url.UrlWithParsedQuery = url.parse(req.url!, /* parseQueryString */ true);
		switch (reqUrl.pathname) {
			case '/signin':
				const receivedNonce: string = (reqUrl.query.nonce?.toString() || '').replace(/ /g, '+');
				if (receivedNonce === nonce) {
					deferredRedirect.resolve({ req, res });
				} else {
					const err = new Error('Nonce does not match.');
					deferredRedirect.resolve({ err, res });
				}
				break;
			case '/':
				sendFile(res, path.join(ext.context.asAbsolutePath('codeFlowResult'), 'index.html'), 'text/html; charset=utf-8');
				break;
			case '/main.css':
				sendFile(res, path.join(ext.context.asAbsolutePath('codeFlowResult'), 'main.css'), 'text/css; charset=utf-8');
				break;
			case '/callback':
				deferredCode.resolve(callback(nonce, reqUrl)
					// eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
					.then(code => ({ code, res }), err => ({ err, res })));
				break;
			default:
				res.writeHead(404);
				res.end();
				break;
		}
	});
	codePromise.then(cancelCodeTimer, cancelCodeTimer);
	return {
		server,
		redirectPromise,
		codePromise,
		codeTimer
	};
}

export function createTerminateServer(server: http.Server): () => Promise<void> {
	const sockets: Record<number, net.Socket> = {};
	let socketCount = 0;
	server.on('connection', socket => {
		const id = socketCount++;
		sockets[id] = socket;
		socket.on('close', () => {
			delete sockets[id];
		});
	});
	return async () => {
		const result = new Promise<void>((resolve: () => void) => server.close(resolve));
		for (const id in sockets) {
			sockets[id].destroy();
		}
		return result;
	};
}

export async function startServer(server: http.Server, adfs: boolean): Promise<number> {
	let portTimer: NodeJS.Timer;
	function cancelPortTimer() {
		clearTimeout(portTimer);
	}
	const portPromise = new Promise<number>((resolve, reject) => {
		portTimer = setTimeout(() => {
			reject(new Error('Timeout waiting for port'));
		}, 5000);
		server.on('listening', () => {
			const address: string | net.AddressInfo | null = server.address();
			if (address && typeof address !== 'string') {
				resolve(address.port);
			}
		});
		server.on('error', err => {
			reject(err);
		});
		server.on('close', () => {
			reject(new Error('Closed'));
		});
		server.listen(adfs ? portADFS : 0, '127.0.0.1');
	});
	portPromise.then(cancelPortTimer, cancelPortTimer);
	return portPromise;
}

function sendFile(res: http.ServerResponse, filepath: string, contentType: string): void {
	fs.readFile(filepath, (err, body) => {
		if (err) {
			logErrorMessage(err);
		} else {
			res.writeHead(200, {
				'Content-Length': body.length,
				'Content-Type': contentType
			});
			res.end(body);
		}
	});
}

async function callback(nonce: string, reqUrl: url.Url): Promise<string> {
	let query: ParsedUrlQuery;
	let error: string | undefined;
	let code: string | undefined;

	if (reqUrl.query) {
		query = typeof reqUrl.query === 'string' ? parse(reqUrl.query) : reqUrl.query;
		error = getQueryProp(query, 'error_description') || getQueryProp(query, 'error');
		code = getQueryProp(query, 'code');

		if (!error) {
			const receivedNonce: string = getQueryProp(query, 'nonce').replace(/ /g, '+');
			if (receivedNonce !== nonce) {
				error = 'Nonce does not match.';
			}
		}
	}

	if (!error && code) {
		return code;
	}

	throw new Error(error || 'No code received.');
}

function getQueryProp(query: ParsedUrlQuery, propName: string): string {
	const value = query[propName];
	return typeof value === 'string' ? value : '';
}

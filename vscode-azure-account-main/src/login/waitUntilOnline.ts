/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { Environment } from "@azure/ms-rest-azure-env";
import * as http from 'http';
import * as https from 'https';
import { CancellationTokenSource } from "vscode";
import { logAttemptingToReachUrlMessage } from "../logAttemptingToReachUrlMessage";
import { logErrorMessage } from "../utils/logErrorMessage";
import { delay } from "../utils/timeUtils";

export async function waitUntilOnline(environment: Environment, interval: number, token = new CancellationTokenSource().token): Promise<void> {
	let checkIsOnlineTask: Promise<boolean> = checkIsOnline(environment);
	let delayTask: Promise<false | PromiseLike<false> | undefined> = delay(interval, false);
	while (!token.isCancellationRequested && !await Promise.race([checkIsOnlineTask, delayTask])) {
		await delayTask;
		checkIsOnlineTask = asyncOr(checkIsOnlineTask, checkIsOnline(environment));
		delayTask = delay(interval, false);
	}
}

async function checkIsOnline(environment: Environment): Promise<boolean> {
	try {
		await new Promise<http.IncomingMessage>((resolve, reject) => {
			const url: string = environment.activeDirectoryEndpointUrl;
			logAttemptingToReachUrlMessage(url);
			(url.startsWith('https:') ? https : http).get(url, resolve)
				.on('error', reject);
		});
		return true;
	} catch (err) {
		logErrorMessage(err);
		return false;
	}
}

async function asyncOr<A, B>(a: Promise<A>, b: Promise<B>): Promise<A | B> {
	return Promise.race([awaitAOrB(a, b), awaitAOrB(b, a)]);
}

async function awaitAOrB<A, B>(a: Promise<A>, b: Promise<B>): Promise<A | B> {
	return (await a) || b;
}

/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

'use strict';

import { callWithTelemetryAndErrorHandling, IActionContext } from '@microsoft/vscode-azext-utils';
import { env, ExtensionContext, extensions, Uri, window } from 'vscode';
import * as nls from 'vscode-nls';

const localize = nls.loadMessageBundle();

const NPS_SURVEY_URL= 'https://www.surveymonkey.com/r/SMQM3DH';

const PROBABILITY = 0.15;
const SESSION_COUNT_KEY = 'nps/sessionCount';
const LAST_SESSION_DATE_KEY = 'nps/lastSessionDate';
const SKIP_VERSION_KEY = 'nps/skipVersion';
const IS_CANDIDATE_KEY = 'nps/isCandidate';

export function survey({ globalState }: ExtensionContext): void {
	void callWithTelemetryAndErrorHandling('azure-account.nps.survey', async (context: IActionContext) => {
		if (env.language !== 'en' && !env.language.startsWith('en-')) {
			return;
		}

		const skipVersion = globalState.get(SKIP_VERSION_KEY, '');
		if (skipVersion) {
			return;
		}

		const date = new Date().toDateString();
		const lastSessionDate = globalState.get(LAST_SESSION_DATE_KEY, new Date(0).toDateString());

		if (date === lastSessionDate) {
			return;
		}

		const sessionCount = globalState.get(SESSION_COUNT_KEY, 0) + 1;
		await globalState.update(LAST_SESSION_DATE_KEY, date);
		await globalState.update(SESSION_COUNT_KEY, sessionCount);

		if (sessionCount < 9) {
			return;
		}

		const isCandidate = globalState.get(IS_CANDIDATE_KEY, false)
			|| Math.random() < PROBABILITY;

		await globalState.update(IS_CANDIDATE_KEY, isCandidate);

		// eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-non-null-assertion
		const extensionVersion = extensions.getExtension('ms-vscode.azure-account')!.packageJSON.version || 'unknown';
		if (!isCandidate) {
			await globalState.update(SKIP_VERSION_KEY, extensionVersion);
			return;
		}

		const take = {
			title: localize('azure-account.takeSurvey', "Take Survey"),
			run: async () => {
				context.telemetry.properties.takeShortSurvey = 'true';
				void env.openExternal(Uri.parse(`${NPS_SURVEY_URL}?o=${encodeURIComponent(process.platform)}&v=${encodeURIComponent(extensionVersion)}&m=${encodeURIComponent(env.machineId)}`));
				await globalState.update(IS_CANDIDATE_KEY, false);
				await globalState.update(SKIP_VERSION_KEY, extensionVersion);
			}
		};
		const remind = {
			title: localize('azure-account.remindLater', "Remind Me Later"),
			run: async () => {
				context.telemetry.properties.remindMeLater = 'true';
				await globalState.update(SESSION_COUNT_KEY, sessionCount - 3);
			}
		};
		const never = {
			title: localize('azure-account.neverAgain', "Don't Show Again"),
			isSecondary: true,
			run: async () => {
				context.telemetry.properties.dontShowAgain = 'true';
				await globalState.update(IS_CANDIDATE_KEY, false);
				await globalState.update(SKIP_VERSION_KEY, extensionVersion);
			}
		};

		context.telemetry.properties.userAsked = 'true';
		const button = await window.showInformationMessage(localize('azure-account.surveyQuestion', "Do you mind taking a quick feedback survey about the Azure Extensions for VS Code?"), take, remind, never);
		await (button || remind).run();
	});
}

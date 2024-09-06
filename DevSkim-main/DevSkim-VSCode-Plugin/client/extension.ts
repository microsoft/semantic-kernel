/* --------------------------------------------------------------------------------------------
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License. See License.txt in the project root for license information.
 * ------------------------------------------------------------------------------------------ */
import * as path from 'path';
import { ExtensionContext } from 'vscode';
import {
	DidChangeConfigurationNotification,
	LanguageClient,
	LanguageClientOptions,
	ServerOptions,
	TransportKind
} from 'vscode-languageclient/node';

import * as vscode from 'vscode';
import { DevSkimSettings, DevSkimSettingsObject } from './common/devskimSettings';
import { getCodeFixMapping, getFileVersion } from './common/notificationNames';
import { selectors } from './common/selectors';
import { DevSkimFixer } from './devSkimFixer';
import { CodeFixMapping } from './common/codeFixMapping';
import { FileVersion } from './common/fileVersion';

let client: LanguageClient;

async function resolveDotNetPath(): Promise<string> {
	const result = await vscode.commands.executeCommand<any>(
		"dotnet.acquire",
		{
			version: "8.0",
			requestingExtensionId: "MS-CST-E.vscode-devskim",
		}
	);
	return result?.dotnetPath;
}

function getDevSkimConfiguration(section='MS-CST-E.vscode-devskim' ): DevSkimSettings {
	const settings: DevSkimSettings = new DevSkimSettingsObject();
	settings.enableCriticalSeverityRules = vscode.workspace.getConfiguration(section).get('rules.enableCriticalSeverityRules', true);
	settings.enableImportantSeverityRules = vscode.workspace.getConfiguration(section).get('rules.enableImportantSeverityRules', true);
	settings.enableModerateSeverityRules = vscode.workspace.getConfiguration(section).get('rules.enableModerateSeverityRules', true);
	settings.enableManualReviewSeverityRules = vscode.workspace.getConfiguration(section).get('rules.enableManualReviewSeverityRules', false);
	settings.enableBestPracticeSeverityRules = vscode.workspace.getConfiguration(section).get('rules.enableBestPracticeSeverityRules', false);
	settings.enableHighConfidenceRules = vscode.workspace.getConfiguration(section).get('rules.enableHighConfidenceRules', true);
	settings.enableMediumConfidenceRules = vscode.workspace.getConfiguration(section).get('rules.enableMediumConfidenceRules', true);
	settings.enableLowConfidenceRules = vscode.workspace.getConfiguration(section).get('rules.enableLowConfidenceRules', false);
	settings.customRulesPaths = vscode.workspace.getConfiguration(section).get('rules.customRulesPath', []);
	settings.customLanguagesPath = vscode.workspace.getConfiguration(section).get('rules.customLanguagesPath', "");
	settings.customCommentsPath = vscode.workspace.getConfiguration(section).get('rules.customCommentsPath', "");
	settings.suppressionDurationInDays = vscode.workspace.getConfiguration(section).get('suppressions.suppressionDurationInDays', 30);
	settings.suppressionCommentStyle = vscode.workspace.getConfiguration(section).get('suppressions.suppressionCommentStyle', 'line');
	settings.manualReviewerName = vscode.workspace.getConfiguration(section).get('suppressions.manualReviewerName', '');
	settings.guidanceBaseURL = vscode.workspace.getConfiguration(section).get('guidance.guidanceBaseURL', "https://github.com/Microsoft/DevSkim/blob/main/guidance/");
	settings.ignoreFiles = vscode.workspace.getConfiguration(section).get('ignores.ignoreFiles',
		[ "out/.*", "bin/.*", "node_modules/.*", ".vscode/.*", "yarn.lock", "logs/.*", ".log", ".git" ]);
	settings.ignoreRulesList = vscode.workspace.getConfiguration(section).get('ignores.ignoreRulesList', []);
	settings.ignoreDefaultRules = vscode.workspace.getConfiguration(section).get('ignores.ignoreDefaultRules', false);
	settings.removeFindingsOnClose = vscode.workspace.getConfiguration(section).get('findings.removeFindingsOnClose', false);
	settings.scanOnOpen = vscode.workspace.getConfiguration(section).get('triggers.scanOnOpen', false);
	settings.scanOnSave = vscode.workspace.getConfiguration(section).get('triggers.scanOnSave', false);
	settings.scanOnChange = vscode.workspace.getConfiguration(section).get('triggers.scanOnChange', true);
	settings.traceServer = vscode.workspace.getConfiguration(section).get('trace.server', false);
	return settings;

}

export function activate(context: ExtensionContext) {
	const config = getDevSkimConfiguration();
	const fixer = new DevSkimFixer();
	context.subscriptions.push(
		vscode.languages.registerCodeActionsProvider(selectors, fixer, {
			providedCodeActionKinds: DevSkimFixer.providedCodeActionKinds
		})
	);

	// The server bridge is implemented in .NET
	const serverModule = context.asAbsolutePath(path.join('devskimBinaries', 'Microsoft.DevSkim.LanguageServer.dll'));
	resolveDotNetPath().then((dotNetPath) =>
	{
		if (dotNetPath == undefined || dotNetPath == null)
		{
			// Error, can't start extension
			// TODO: Notify user
		}
		else
		{
			const workPath = path.dirname(serverModule);
			const serverOptions: ServerOptions = {
				run: { 
					command: dotNetPath, 
					args: [serverModule], 
					options: {cwd: workPath},
					transport: TransportKind.pipe
				},
				debug: { 
					command: dotNetPath, 
					args: [serverModule], 
					options: {cwd: workPath},
					transport: TransportKind.pipe
				}
			};
	
			// Options to control the language client
			const clientOptions: LanguageClientOptions = {
				documentSelector: selectors,
				progressOnInitialization: true
			};
	
			client = new LanguageClient(
				'MS-CST-E.vscode-devskim',
				'DevSkim VS Code Client',
				serverOptions,
				clientOptions
			);

			 // Start the client. This will also launch the server
			client.registerProposedFeatures();
			const disposable = client.start();
			
			client.onReady().then(() => 
				{
					client.onNotification(getCodeFixMapping(), (mapping: CodeFixMapping) => 
					{
						fixer.ensureMapHasMappings(mapping);
					});
					client.onNotification(getFileVersion(), (fileversion: FileVersion) =>{
						fixer.removeFindingsForOtherVersions(fileversion);
					});
					client.sendNotification(DidChangeConfigurationNotification.type, { settings: ""});
				}
			);

			vscode.workspace.onDidChangeConfiguration(e => {
				if (e.affectsConfiguration("MS-CST-E.vscode-devskim"))
				{
					// Triggers server to query for client config.
					// Hacky, but vscode insists a pull model should be used over a push model for transmitting settings.
					client.sendNotification(DidChangeConfigurationNotification.type, { settings: "" });
				}
			});

			// For disposal of the client
			context.subscriptions.push(disposable);
		}
	});
}

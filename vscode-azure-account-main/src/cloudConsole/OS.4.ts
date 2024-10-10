import { callWithTelemetryAndErrorHandlingSync, IActionContext, IParsedError, parseError } from '@microsoft/vscode-azext-utils';
import * as cp from 'child_process';
import * as FormData from 'form-data';
import { ReadStream } from 'fs';
import * as http from 'http';
import { ClientRequest } from 'http';
import { Socket } from 'net';
import { Response } from 'node-fetch';
import * as path from 'path';
import * as request from 'request-promise';
import * as semver from 'semver';
import { parse, UrlWithStringQuery } from 'url';
import { v4 as uuid } from 'uuid';
import { CancellationToken, commands, Disposable, env, EventEmitter, MessageItem, QuickPickItem, Terminal, TerminalOptions, TerminalProfile, ThemeIcon, UIKind, Uri, version, window, workspace } from 'vscode';
import { AzureAccountExtensionApi, AzureLoginStatus, AzureSession, CloudShell, CloudShellStatus, UploadOptions } from '../azure-account.api';
import { AzureSession as AzureSessionLegacy } from '../azure-account.legacy.api';
import { ext } from '../extensionVariables';
import { logAttemptingToReachUrlMessage } from '../logAttemptingToReachUrlMessage';
import { tokenFromRefreshToken } from '../login/adal/tokens';
import { getAuthLibrary } from '../login/getAuthLibrary';
import { localize } from '../utils/localize';
import { logErrorMessage } from '../utils/logErrorMessage';
import { HttpLogger } from '../utils/logging/HttpLogger';
import { fetchWithLogging } from '../utils/logging/nodeFetch/nodeFetch';
import { RequestNormalizer } from '../utils/logging/request/RequestNormalizer';
import { Deferred } from '../utils/promiseUtils';
import { delay } from '../utils/timeUtils';
import { CloudShellInternal } from "./CloudShellInternal.1";
import { createServer, Queue, readJSON, Server } from './createServer';

interface OS {
    id: 'linux' | 'windows';
    shellName: string;
    otherOS: OS;
}

export type OSName = 'Linux' | 'Windows';
type OSes = { Linux: OS; Windows: OS; };

export const OSes: OSes = {
    Linux: {
        id: 'linux',
        shellName: localize('azure-account.bash', "Bash"),
        // eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
        get otherOS(): OS { return OSes.Windows; },
    },
    Windows: {
        id: 'windows',
        shellName: localize('azure-account.powershell', "PowerShell"),
        // eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
        get otherOS(): OS { return OSes.Linux; },
    }
};

async function waitForConnection(this: CloudShell): Promise<boolean> {
    const handleStatus = () => {
        switch (this.status) {
            case 'Connecting':
                return new Promise<boolean>(resolve => {
                    const subs = this.onStatusChanged(() => {
                        subs.dispose();
                        resolve(handleStatus());
                    });
                });
            case 'Connected':
                return true;
            case 'Disconnected':
                return false;
            default:
                const status: never = this.status;
                throw new Error(`Unexpected status '${status}'`);
        }
    };
    return handleStatus();
}
function getUploadFile(tokens: Promise<AccessTokens>, uris: Promise<ConsoleUris>): (this: CloudShell, filename: string, stream: ReadStream, options?: UploadOptions) => Promise<void> {
    return async function (this: CloudShell, filename: string, stream: ReadStream, options: UploadOptions = {}) {
        if (options.progress) {
            options.progress.report({ message: localize('azure-account.connectingForUpload', "Connecting to upload '{0}'...", filename) });
        }

        const accessTokens: AccessTokens = await tokens;
        const { terminalUri } = await uris;

        if (options.token && options.token.isCancellationRequested) {
            throw 'canceled';
        }

        return new Promise<void>((resolve, reject) => {
            const form = new FormData();
            form.append('uploading-file', stream, {
                filename,
                knownLength: options.contentLength
            });
            const uploadUri: string = `${terminalUri}/upload`;
            logAttemptingToReachUrlMessage(uploadUri);
            const uri: UrlWithStringQuery = parse(uploadUri);
            const req: ClientRequest = form.submit(
                {
                    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-explicit-any
                    protocol: <any>uri.protocol,
                    hostname: uri.hostname,
                    port: uri.port,
                    path: uri.path,
                    headers: {
                        'Authorization': `Bearer ${accessTokens.resource}`
                    },
                },
                (err, res) => {
                    if (err) {
                        reject(err);
                    } if (res && res.statusCode && (res.statusCode < 200 || res.statusCode > 299)) {
                        reject(`${res.statusMessage} (${res.statusCode})`);
                    } else {
                        resolve();
                    }
                    if (res) {
                        res.resume(); // Consume response.
                    }
                }
            );

            if (options.token) {
                options.token.onCancellationRequested(() => {
                    reject('canceled');
                    req.abort();
                });
            }
            if (options.progress) {
                req.on('socket', (socket: Socket) => {
                    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                    options.progress!.report({
                        message: localize('azure-account.uploading', "Uploading '{0}'...", filename),
                        increment: 0
                    });

                    let previous: number = 0;
                    socket.on('drain', () => {
                        const total: number = req.getHeader('Content-Length') as number;
                        if (total) {
                            const worked: number = Math.min(Math.round(100 * socket.bytesWritten / total), 100);
                            const increment: number = worked - previous;
                            if (increment) {
                                // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                                options.progress!.report({
                                    message: localize('azure-account.uploading', "Uploading '{0}'...", filename),
                                    increment
                                });
                            }
                            previous = worked;
                        }
                    });
                });
            }
        });
    };
}

export const shells: CloudShellInternal[] = [];
export function createCloudConsole(api: AzureAccountExtensionApi, osName: OSName, terminalProfileToken?: CancellationToken): CloudShellInternal {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    return (callWithTelemetryAndErrorHandlingSync('azure-account.createCloudConsole', (context: IActionContext) => {
        const os: OS = OSes[osName];
        context.telemetry.properties.cloudShellType = os.shellName;

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        let liveServerQueue: Queue<any> | undefined;
        const event: EventEmitter<CloudShellStatus> = new EventEmitter<CloudShellStatus>();
        let deferredTerminal: Deferred<Terminal>;
        let deferredTerminalProfile: Deferred<TerminalProfile>;
        let deferredSession: Deferred<AzureSession>;
        let deferredTokens: Deferred<AccessTokens>;
        const tokensPromise: Promise<AccessTokens> = new Promise<AccessTokens>((resolve, reject) => deferredTokens = { resolve, reject });
        let deferredUris: Deferred<ConsoleUris>;
        const urisPromise: Promise<ConsoleUris> = new Promise<ConsoleUris>((resolve, reject) => deferredUris = { resolve, reject });
        let deferredInitialSize: Deferred<Size>;
        const initialSizePromise: Promise<Size> = new Promise<Size>((resolve, reject) => deferredInitialSize = { resolve, reject });
        const state: CloudShellInternal = {
            status: 'Connecting',
            onStatusChanged: event.event,
            waitForConnection,
            terminal: new Promise<Terminal>((resolve, reject) => deferredTerminal = { resolve, reject }),
            terminalProfile: new Promise<TerminalProfile>((resolve, reject) => deferredTerminalProfile = { resolve, reject }),
            session: new Promise<AzureSession>((resolve, reject) => deferredSession = { resolve, reject }),
            uploadFile: getUploadFile(tokensPromise, urisPromise)
        };

        // eslint-disable-next-line @typescript-eslint/no-empty-function
        state.terminal?.catch(() => { }); // ignore





        // eslint-disable-next-line @typescript-eslint/no-empty-function
        state.session.catch(() => { }); // ignore
        shells.push(state);

        function updateStatus(status: CloudShellStatus) {
            state.status = status;
            event.fire(state.status);
            if (status === 'Disconnected') {
                deferredTerminal.reject(status);
                deferredTerminalProfile.reject(status);
                deferredSession.reject(status);
                deferredTokens.reject(status);
                deferredUris.reject(status);
                shells.splice(shells.indexOf(state), 1);
                void commands.executeCommand('setContext', 'openCloudConsoleCount', `${shells.length}`);
            }
        }

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (async function (): Promise<any> {
            if (!workspace.isTrusted) {
                updateStatus('Disconnected');
                return requiresWorkspaceTrust(context);
            }

            void commands.executeCommand('setContext', 'openCloudConsoleCount', `${shells.length}`);

            const isWindows: boolean = process.platform === 'win32';
            if (isWindows) {
                // See below
                try {
                    const { stdout } = await exec('node.exe --version');
                    const version: string | boolean = stdout[0] === 'v' && stdout.substr(1).trim();
                    if (version && semver.valid(version) && !semver.gte(version, '6.0.0')) {
                        updateStatus('Disconnected');
                        return requiresNode(context);
                    }
                } catch (err) {
                    updateStatus('Disconnected');
                    return requiresNode(context);
                }
            }

            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const serverQueue: Queue<any> = new Queue<any>();
            // eslint-disable-next-line @typescript-eslint/no-misused-promises
            const server: Server = await createServer('vscode-cloud-console', async (req, res) => {
                let dequeue: boolean = false;
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                for (const message of await readJSON<any>(req)) {
                    /* eslint-disable @typescript-eslint/no-unsafe-member-access */
                    if (message.type === 'poll') {
                        dequeue = true;
                    } else if (message.type === 'log') {
                        Array.isArray(message.args) && ext.outputChannel.appendLog((<string[]>message.args).join(' '));
                    } else if (message.type === 'size') {
                        deferredInitialSize.resolve(message.size);
                    } else if (message.type === 'status') {
                        updateStatus(message.status);
                    }
                    /* eslint-enable @typescript-eslint/no-unsafe-member-access */
                }

                let response = [];
                if (dequeue) {
                    try {
                        response = await serverQueue.dequeue(60000);
                    } catch (err) {
                        // ignore timeout
                    }
                }
                res.write(JSON.stringify(response));
                res.end();
            });

            // open terminal
            let shellPath: string = path.join(ext.context.asAbsolutePath('bin'), `node.${isWindows ? 'bat' : 'sh'}`);
            let cloudConsoleLauncherPath: string = path.join(ext.context.asAbsolutePath('dist'), 'cloudConsoleLauncher');
            if (isWindows) {
                cloudConsoleLauncherPath = cloudConsoleLauncherPath.replace(/\\/g, '\\\\');
            }
            const shellArgs: string[] = [
                process.argv0,
                '-e',
                `require('${cloudConsoleLauncherPath}').main()`,
            ];

            if (isWindows) {
                // Work around https://github.com/electron/electron/issues/4218 https://github.com/nodejs/node/issues/11656
                shellPath = 'node.exe';
                shellArgs.shift();
            }

            // Only add flag if in Electron process https://github.com/microsoft/vscode-azure-account/pull/684
            if (!isWindows && !!process.versions['electron'] && env.uiKind === UIKind.Desktop && semver.gte(version, '1.62.1')) {
                // https://github.com/microsoft/vscode/issues/136987
                // This fix can't be applied to all versions of VS Code. An error is thrown in versions less than the one specified
                shellArgs.push('--ms-enable-electron-run-as-node');
            }

            const terminalOptions: TerminalOptions = {
                name: localize('azureCloudShell', 'Azure Cloud Shell ({0})', os.shellName),
                iconPath: new ThemeIcon('azure'),
                shellPath,
                shellArgs,
                env: {
                    CLOUD_CONSOLE_IPC: server.ipcHandlePath,
                },
                isTransient: true
            };

            const cleanupCloudShell = () => {
                liveServerQueue = undefined;
                server.dispose();
                updateStatus('Disconnected');
            };

            // Open the appropriate type of VS Code terminal depending on the entry point
            if (terminalProfileToken) {
                // Entry point: Terminal profile provider
                const terminalProfileCloseSubscription = terminalProfileToken.onCancellationRequested(() => {
                    terminalProfileCloseSubscription.dispose();
                    cleanupCloudShell();
                });

                // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                deferredTerminalProfile!.resolve(new TerminalProfile(terminalOptions));
            } else {
                // Entry point: Extension API
                const terminal: Terminal = window.createTerminal(terminalOptions);
                const terminalCloseSubscription = window.onDidCloseTerminal(t => {
                    if (t === terminal) {
                        terminalCloseSubscription.dispose();
                        cleanupCloudShell();
                    }
                });

                // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                deferredTerminal!.resolve(terminal);
            }

            liveServerQueue = serverQueue;

            if (getAuthLibrary() === 'MSAL') {
                serverQueue.push({ type: 'log', args: [localize('azure-account.doesNotSupportMsal', 'Cloud Shell does not currently support authenticating with MSAL. Please set the "azure.authenticationLibrary" setting to "ADAL" and try again.')] });
                return;
            }

            const loginStatus: AzureLoginStatus = await waitForLoginStatus(api);
            if (loginStatus !== 'LoggedIn') {
                if (loginStatus === 'LoggingIn') {
                    serverQueue.push({ type: 'log', args: [localize('azure-account.loggingIn', "Signing in...")] });
                }
                if (!(await api.waitForLogin())) {
                    serverQueue.push({ type: 'log', args: [localize('azure-account.loginNeeded', "Sign in needed.")] });
                    context.telemetry.properties.outcome = 'requiresLogin';
                    await commands.executeCommand('azure-account.askForLogin');
                    if (!(await api.waitForLogin())) {
                        serverQueue.push({ type: 'exit' });
                        updateStatus('Disconnected');
                        return;
                    }
                }
            }

            let token: Token | undefined = undefined;
            await api.waitForSubscriptions();
            const sessions: AzureSession[] = [...new Set(api.subscriptions.map(subscription => subscription.session))]; // Only consider those with at least one subscription.
            if (sessions.length > 1) {
                serverQueue.push({ type: 'log', args: [localize('azure-account.selectDirectory', "Select directory...")] });

                const fetchingDetails: Promise<({
                    session: AzureSession;
                    tenantDetails: TenantDetails;
                } | undefined)[]> = Promise.all(sessions.map(session => fetchTenantDetails(<AzureSession>session)
                    .catch(err => {
                        logErrorMessage(err);
                        return undefined;
                    })))
                    .then(tenantDetails => tenantDetails.filter(details => details));

                const pick = await window.showQuickPick<QuickPickItem & { session: AzureSession; }>(fetchingDetails
                    .then(tenantDetails => tenantDetails.map(details => {
                        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                        const tenantDetails: TenantDetails = details!.tenantDetails;
                        const defaultDomainName: string | undefined = tenantDetails.defaultDomain;
                        return {
                            label: tenantDetails.displayName,
                            description: defaultDomainName,
                            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                            session: details!.session
                        };
                    }).sort((a, b) => a.label.localeCompare(b.label))), {
                    placeHolder: localize('azure-account.selectDirectoryPlaceholder', "Select directory"),
                    ignoreFocusOut: true // The terminal opens concurrently and can steal focus (https://github.com/microsoft/vscode-azure-account/issues/77).
                });
                if (!pick) {
                    context.telemetry.properties.outcome = 'noTenantPicked';
                    serverQueue.push({ type: 'exit' });
                    updateStatus('Disconnected');
                    return;
                }
                token = await acquireToken(pick.session);
            } else if (sessions.length === 1) {
                token = await acquireToken(<AzureSession>sessions[0]);
            }

            const result = token && await findUserSettings(token);
            if (!result) {
                serverQueue.push({ type: 'log', args: [localize('azure-account.setupNeeded', "Setup needed.")] });
                await requiresSetUp(context);
                serverQueue.push({ type: 'exit' });
                updateStatus('Disconnected');
                return;
            }
            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
            deferredSession!.resolve(result.token.session);

            // provision
            let consoleUri: string;
            const session: AzureSession = result.token.session;
            const accessToken: string = result.token.accessToken;
            const armEndpoint: string = session.environment.resourceManagerEndpointUrl;
            logAttemptingToReachUrlMessage(armEndpoint);
            const provisionTask: () => Promise<void> = async () => {
                consoleUri = await provisionConsole(accessToken, armEndpoint, result.userSettings, OSes.Linux.id);
                context.telemetry.properties.outcome = 'provisioned';
            };
            try {
                serverQueue.push({ type: 'log', args: [localize('azure-account.requestingCloudConsole', "Requesting a Cloud Shell...")] });
                await provisionTask();
            } catch (err) {
                if (parseError(err).message === Errors.DeploymentOsTypeConflict) {
                    const reset = await deploymentConflict(context, os);
                    if (reset) {
                        await resetConsole(accessToken, armEndpoint);
                        return provisionTask();
                    } else {
                        serverQueue.push({ type: 'exit' });
                        updateStatus('Disconnected');
                        return;
                    }
                } else {
                    throw err;
                }
            }

            const keyVaultToken = session.environment.keyVaultDnsSuffix
                // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                ? await tokenFromRefreshToken(session.environment, result.token.refreshToken, session.tenantId, `https://${session.environment.keyVaultDnsSuffix!.substr(1)}`)
                : undefined;
            const accessTokens: AccessTokens = {
                resource: accessToken,
                keyVault: keyVaultToken && keyVaultToken.accessToken
            };
            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
            deferredTokens!.resolve(accessTokens);

            // Connect to terminal
            const connecting: string = localize('azure-account.connectingTerminal', "Connecting terminal...");
            serverQueue.push({ type: 'log', args: [connecting] });
            const progressTask: (i: number) => void = (i: number) => {
                serverQueue.push({ type: 'log', args: [`\x1b[A${connecting}${'.'.repeat(i)}`] });
            };
            const initialSize: Size = await initialSizePromise;
            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
            const consoleUris: ConsoleUris = await connectTerminal(accessTokens, consoleUri!, /* TODO: Separate Shell from OS */ osName === 'Linux' ? 'bash' : 'pwsh', initialSize, progressTask);
            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
            deferredUris!.resolve(consoleUris);

            // Connect to WebSocket
            serverQueue.push({
                type: 'connect',
                accessTokens,
                consoleUris
            });
        })().catch(err => {
            const parsedError: IParsedError = parseError(err);
            ext.outputChannel.appendLog(parsedError.message);
            parsedError.stack && ext.outputChannel.appendLog(parsedError.stack);
            updateStatus('Disconnected');
            context.telemetry.properties.outcome = 'error';
            context.telemetry.properties.message = parsedError.message;
            if (liveServerQueue) {
                liveServerQueue.push({ type: 'log', args: [localize('azure-account.error', "Error: {0}", parsedError.message)] });
            }
        });
        return state;
    }))!;
}

async function waitForLoginStatus(api: AzureAccountExtensionApi): Promise<AzureLoginStatus> {
    if (api.status !== 'Initializing') {
        return api.status;
    }
    return new Promise<AzureLoginStatus>(resolve => {
        const subscription: Disposable = api.onStatusChanged(() => {
            subscription.dispose();
            resolve(waitForLoginStatus(api));
        });
    });
}

async function findUserSettings(token: Token): Promise<{ userSettings: UserSettings; token: Token; } | undefined> {
    const userSettings: UserSettings | undefined = await getUserSettings(token.accessToken, token.session.environment.resourceManagerEndpointUrl);
    // Valid settings will have either a storage profile (mounted) or a session type of 'Ephemeral'.
    if (userSettings && (userSettings.storageProfile || userSettings.sessionType === 'Ephemeral')) {
        return { userSettings, token };
    }
}

async function requiresSetUp(context: IActionContext) {
    context.telemetry.properties.outcome = 'requiresSetUp';
    const open: MessageItem = { title: localize('azure-account.open', "Open") };
    const message: string = localize('azure-account.setUpInWeb', "First launch of Cloud Shell in a directory requires setup in the web application (https://shell.azure.com).");
    const response: MessageItem | undefined = await window.showInformationMessage(message, open);
    if (response === open) {
        context.telemetry.properties.outcome = 'requiresSetUpOpen';
        void env.openExternal(Uri.parse('https://shell.azure.com'));
    } else {
        context.telemetry.properties.outcome = 'requiresSetUpCancel';
    }
}

async function requiresNode(context: IActionContext) {
    context.telemetry.properties.outcome = 'requiresNode';
    const open: MessageItem = { title: localize('azure-account.open', "Open") };
    const message: string = localize('azure-account.requiresNode', "Opening a Cloud Shell currently requires Node.js 6 or later to be installed (https://nodejs.org).");
    const response: MessageItem | undefined = await window.showInformationMessage(message, open);
    if (response === open) {
        context.telemetry.properties.outcome = 'requiresNodeOpen';
        void env.openExternal(Uri.parse('https://nodejs.org'));
    } else {
        context.telemetry.properties.outcome = 'requiresNodeCancel';
    }
}

async function requiresWorkspaceTrust(context: IActionContext) {
    context.telemetry.properties.outcome = 'requiresWorkspaceTrust';
    const ok: MessageItem = { title: localize('azure-account.ok', "OK") };
    const message: string = localize('azure-account.cloudShellRequiresTrustedWorkspace', 'Opening a Cloud Shell only works in a trusted workspace.');
    return await window.showInformationMessage(message, ok) === ok;
}

async function deploymentConflict(context: IActionContext, os: OS) {
    context.telemetry.properties.outcome = 'deploymentConflict';
    const ok: MessageItem = { title: localize('azure-account.ok', "OK") };
    const message: string = localize('azure-account.deploymentConflict', "Starting a {0} session will terminate all active {1} sessions. Any running processes in active {1} sessions will be terminated.", os.shellName, os.otherOS.shellName);
    const response: MessageItem | undefined = await window.showWarningMessage(message, ok);
    const reset: boolean = response === ok;
    context.telemetry.properties.outcome = reset ? 'deploymentConflictReset' : 'deploymentConflictCancel';
    return reset;
}
interface Token {
    session: AzureSession;
    accessToken: string;
    refreshToken: string;
}

async function acquireToken(session: AzureSession): Promise<Token> {
    return new Promise<Token>((resolve, reject) => {
        /* eslint-disable @typescript-eslint/no-explicit-any */
        const credentials: any = (<AzureSessionLegacy>session).credentials;
        const environment: any = session.environment;
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
        credentials.context.acquireToken(environment.activeDirectoryResourceId, credentials.username, credentials.clientId, function (err: any, result: any) {
            /* eslint-enable @typescript-eslint/no-explicit-any */
            if (err) {
                reject(err);
            } else {
                resolve({
                    session,
                    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access
                    accessToken: result.accessToken,
                    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access
                    refreshToken: result.refreshToken
                });
            }
        });
    });
}
interface TenantDetails {
    objectId: string;
    displayName: string;
    domains: string;
    defaultDomain: string;
}

async function fetchTenantDetails(session: AzureSession): Promise<{ session: AzureSession; tenantDetails: TenantDetails; }> {

    const response: Response = await fetchWithLogging('https://management.azure.com/tenants?api-version=2022-12-01', {
        headers: {
            Authorization: `Bearer ${(await session.credentials2.getToken([]))?.token}`,
            "x-ms-client-request-id": uuid(),
            "Content-Type": 'application/json; charset=utf-8'
        }
    });

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    const json = await response.json();
    return {
        session,
        // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access
        tenantDetails: json.value[0]
    };
}

export interface ExecResult {
    error: Error | null;
    stdout: string;
    stderr: string;
}


async function exec(command: string): Promise<ExecResult> {
    return new Promise<ExecResult>((resolve, reject) => {
        cp.exec(command, (error, stdout, stderr) => {
            (error || stderr ? reject : resolve)({ error, stdout, stderr });
        });
    });
}
const consoleApiVersion = '2023-02-01-preview';

export enum Errors {
    DeploymentOsTypeConflict = 'DeploymentOsTypeConflict'
}
function getConsoleUri(armEndpoint: string) {
    return `${armEndpoint}/providers/Microsoft.Portal/consoles/default?api-version=${consoleApiVersion}`;
}

export interface UserSettings {
    preferredLocation: string;
    preferredOsType: string; // The last OS chosen in the portal.





    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    storageProfile: any;
    sessionType: 'Ephemeral' | 'Mounted';
}

export interface AccessTokens {
    resource: string;
    // graph: string;
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
// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function requestWithLogging(requestOptions: request.Options): Promise<any> {
    try {
        const requestLogger = new HttpLogger(ext.outputChannel, 'CloudConsoleLauncher', new RequestNormalizer());
        requestLogger.logRequest(requestOptions);
        // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
        const response: http.IncomingMessage & { body: unknown; } = await request(requestOptions);
        requestLogger.logResponse({ response, request: requestOptions });
        // eslint-disable-next-line @typescript-eslint/no-unsafe-return
        return response;
    } catch (e) {
        const error = parseError(e);
        ext.outputChannel.error({ ...error, name: 'Request Error: CloudConsoleLauncher' });
    }
}

export async function getUserSettings(accessToken: string, armEndpoint: string): Promise<UserSettings | undefined> {
    const targetUri = `${armEndpoint}/providers/Microsoft.Portal/userSettings/cloudconsole?api-version=${consoleApiVersion}`;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    const response = await requestWithLogging({
        uri: targetUri,
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`
        },
        simple: false,
        resolveWithFullResponse: true,
        json: true,
    });

    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    if (response.statusCode < 200 || response.statusCode > 299) {
        // if (response.body && response.body.error && response.body.error.message) {
        // 	console.log(`${response.body.error.message} (${response.statusCode})`);
        // } else {
        // 	console.log(response.statusCode, response.headers, response.body);
        // }
        return;
    }

    // eslint-disable-next-line @typescript-eslint/no-unsafe-return, @typescript-eslint/no-unsafe-member-access
    return response.body && response.body.properties;
}
/* eslint-disable @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-assignment */
export async function provisionConsole(accessToken: string, armEndpoint: string, userSettings: UserSettings, osType: string): Promise<string> {
    let response = await createTerminal(accessToken, armEndpoint, userSettings, osType, true);
    for (let i = 0; i < 10; i++, response = await createTerminal(accessToken, armEndpoint, userSettings, osType, false)) {
        if (response.statusCode < 200 || response.statusCode > 299) {
            if (response.statusCode === 409 && response.body && response.body.error && response.body.error.code === Errors.DeploymentOsTypeConflict) {
                throw new Error(Errors.DeploymentOsTypeConflict);
            } else if (response.body && response.body.error && response.body.error.message) {
                throw new Error(`${response.body.error.message} (${response.statusCode})`);
            } else {
                throw new Error(`${response.statusCode} ${response.headers} ${response.body}`);
            }
        }

        const consoleResource = response.body;
        if (consoleResource.properties.provisioningState === 'Succeeded') {
            // eslint-disable-next-line @typescript-eslint/no-unsafe-return
            return consoleResource.properties.uri;
        } else if (consoleResource.properties.provisioningState === 'Failed') {
            break;
        }
    }
    throw new Error(`Sorry, your Cloud Shell failed to provision. Please retry later. Request correlation id: ${response.headers['x-ms-routing-request-id']}`);
}
/* eslint-enable @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-assignment */
async function createTerminal(accessToken: string, armEndpoint: string, userSettings: UserSettings, osType: string, initial: boolean) {
    return requestWithLogging({
        uri: getConsoleUri(armEndpoint),
        method: initial ? 'PUT' : 'GET',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
            'x-ms-console-preferred-location': userSettings.preferredLocation
        },
        simple: false,
        resolveWithFullResponse: true,
        json: true,
        body: initial ? {
            properties: {
                osType
            }
        } : undefined
    });
}
// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export async function resetConsole(accessToken: string, armEndpoint: string) {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    const response = await requestWithLogging({
        uri: getConsoleUri(armEndpoint),
        method: 'DELETE',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`
        },
        simple: false,
        resolveWithFullResponse: true,
        json: true
    });

    /* eslint-disable @typescript-eslint/no-unsafe-member-access */
    if (response.statusCode < 200 || response.statusCode > 299) {
        if (response.body && response.body.error && response.body.error.message) {
            throw new Error(`${response.body.error.message} (${response.statusCode})`);
        } else {
            throw new Error(`${response.statusCode} ${response.headers} ${response.body}`);
        }
    }
    /* eslint-enable @typescript-eslint/no-unsafe-member-access */
}

export async function connectTerminal(accessTokens: AccessTokens, consoleUri: string, shellType: string, initialSize: Size, progress: (i: number) => void): Promise<ConsoleUris> {

    for (let i = 0; i < 10; i++) {
        /* eslint-disable @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-assignment */
        const response = await initializeTerminal(accessTokens, consoleUri, shellType, initialSize);

        if (response.statusCode < 200 || response.statusCode > 299) {
            if (response.statusCode !== 503 && response.statusCode !== 504 && response.body && response.body.error) {
                if (response.body && response.body.error && response.body.error.message) {
                    throw new Error(`${response.body.error.message} (${response.statusCode})`);
                } else {
                    throw new Error(`${response.statusCode} ${response.headers} ${response.body}`);
                }
            }
            await delay(1000 * (i + 1));
            progress(i + 1);
            continue;
        }

        const { id, socketUri } = response.body;
        const terminalUri = `${consoleUri}/terminals/${id}`;
        return {
            consoleUri,
            terminalUri,
            socketUri
        };
        /* eslint-enable @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-assignment */
    }

    throw new Error('Failed to connect to the terminal.');
}

async function initializeTerminal(accessTokens: AccessTokens, consoleUri: string, shellType: string, initialSize: Size) {
    const consoleUrl = new URL(consoleUri);
    return requestWithLogging({
        // eslint-disable-next-line @typescript-eslint/restrict-plus-operands
        uri: consoleUri + '/terminals?cols=' + initialSize.cols + '&rows=' + initialSize.rows + '&shell=' + shellType,
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': `Bearer ${accessTokens.resource}`,
            'Referer': consoleUrl.protocol + "//" + consoleUrl.hostname + '/$hc' + consoleUrl.pathname + '/terminals',
        },
        simple: false,
        resolveWithFullResponse: true,
        json: true,
        body: {
            tokens: accessTokens.keyVault ? [accessTokens.keyVault] : []
        }
    });
}

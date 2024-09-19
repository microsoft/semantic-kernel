import { WebSiteManagementClient } from '@azure/arm-appservice';
import { ResourceManagementClient } from '@azure/arm-resources';
import { SubscriptionClient, SubscriptionModels } from '@azure/arm-subscriptions';
import type { AzureExtensionApiProvider } from '@microsoft/vscode-azext-utils/api';
import { ExtensionContext, QuickPickItem, commands, extensions, window } from 'vscode';
import { AzureAccountExtensionApi, AzureSession } from '../../src/azure-account.api';




export function activate(context: ExtensionContext): void {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const azureAccount: AzureAccountExtensionApi = (<AzureExtensionApiProvider>extensions.getExtension('ms-vscode.azure-account')!.exports).getApi('1.0.0');
    const subscriptions = context.subscriptions;
    subscriptions.push(commands.registerCommand('azure-account-sample.showSubscriptions', showSubscriptions(azureAccount)));
    subscriptions.push(commands.registerCommand('azure-account-sample.showAppServices', showAppServices(azureAccount)));
}
interface SubscriptionItem {
    label: string;
    description: string;
    session: AzureSession;
    subscription: SubscriptionModels.Subscription;
}
function showSubscriptions(api: AzureAccountExtensionApi) {
    return async () => {
        if (!(await api.waitForLogin())) {
            return commands.executeCommand('azure-account.askForLogin');
        }
        const subscriptionItems = loadSubscriptionItems(api);
        const result = await window.showQuickPick(subscriptionItems);
        if (result) {
            const resourceGroupItems = loadResourceGroupItems(result);
            await window.showQuickPick(resourceGroupItems);
        }
    };
}

async function loadSubscriptionItems(api: AzureAccountExtensionApi) {
    await api.waitForFilters();
    const subscriptionItems: SubscriptionItem[] = [];
    for (const session of api.sessions) {
        const credentials = session.credentials2;
        const subscriptionClient = new SubscriptionClient(credentials);
        const subscriptions = await listAll(subscriptionClient.subscriptions, subscriptionClient.subscriptions.list());
        subscriptionItems.push(...subscriptions.map(subscription => ({
            label: subscription.displayName || '',
            description: subscription.subscriptionId || '',
            session,
            subscription
        })));
    }
    subscriptionItems.sort((a, b) => a.label.localeCompare(b.label));
    return subscriptionItems;
}

async function loadResourceGroupItems(subscriptionItem: SubscriptionItem) {
    const { session, subscription } = subscriptionItem;
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const resources = new ResourceManagementClient(session.credentials2, subscription.subscriptionId!);
    const resourceGroups = await listAll(resources.resourceGroups, resources.resourceGroups.list());
    resourceGroups.sort((a, b) => (a.name || '').localeCompare(b.name || ''));
    return resourceGroups.map(resourceGroup => ({
        label: resourceGroup.name || '',
        description: resourceGroup.location,
        resourceGroup
    }));
}
function showAppServices(api: AzureAccountExtensionApi) {
    return async () => {
        if (!(await api.waitForLogin())) {
            return commands.executeCommand('azure-account.askForLogin');
        }
        const webAppItems = loadWebAppItems(api);
        await window.showQuickPick(webAppItems);
    };
}

async function loadWebAppItems(api: AzureAccountExtensionApi) {
    await api.waitForFilters();
    const webAppsPromises: Promise<QuickPickItem[]>[] = [];
    for (const filter of api.filters) {
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        const client = new WebSiteManagementClient(filter.session.credentials2, filter.subscription.subscriptionId!);
        webAppsPromises.push(listAll(client.webApps, client.webApps.list())
            .then(webApps => webApps.map(webApp => {
                return {
                    label: webApp.name || '',
                    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                    description: filter.subscription.displayName!,
                    webApp
                };
            })));
    }
    const webApps = (<QuickPickItem[]>[]).concat(...(await Promise.all(webAppsPromises)));
    webApps.sort((a, b) => a.label.localeCompare(b.label));
    return webApps;
}

export function deactivate(): void {
    return;
}

export interface PartialList<T> extends Array<T> {
    nextLink?: string;
}

async function listAll<T>(client: { listNext(nextPageLink: string): Promise<PartialList<T>>; }, first: Promise<PartialList<T>>): Promise<T[]> {
    const all: T[] = [];
    for (let list = await first; list.length || list.nextLink; list = list.nextLink ? await client.listNext(list.nextLink) : []) {
        all.push(...list);
    }
    return all;
}

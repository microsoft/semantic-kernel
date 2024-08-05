import { IActionContext } from "@microsoft/vscode-azext-utils";
import { ext } from "../extensionVariables";
import { selectSubscriptions } from "../login/commands/selectSubscriptions";
import { localize } from "../utils/localize";

export async function manageAccount(context: IActionContext): Promise<void> {
    const signOutPick = {
        label: localize('signOut', 'Sign Out'),
    };

    const selectSubscriptionsPick = {
        label: localize('selectSubscriptions', 'Select Subscriptions...'),
    };

    const result = await context.ui.showQuickPick(
        [selectSubscriptionsPick, signOutPick],
        {
            stepName: 'selectSubscriptionsOrSignOut',
            placeHolder: localize('signedInAs', 'Signed in as {0}', ext.loginHelper.api.sessions[0].userId),
            canPickMany: false,
        },
    );

    if (result === signOutPick) {
        await ext.loginHelper.logout();
    } else if (result === selectSubscriptionsPick) {
        await selectSubscriptions(context);
    }
}

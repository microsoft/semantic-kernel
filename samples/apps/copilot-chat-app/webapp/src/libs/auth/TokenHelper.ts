import {
    IPublicClientApplication,
    InteractionRequiredAuthError,
    InteractionStatus,
    PopupRequest,
} from '@azure/msal-browser';

enum TokenErrors {
    InteractionInProgress = 'interaction_in_progress',
}

/*
 * This implementation follows incremental consent, and token acquisition is limited to one
 * resource at a time (scopes), but user can consent to many resources upfront (extraScopesToConsent)
 */
export const getAccessTokenUsingMsal = async (
    inProgress: InteractionStatus,
    msalInstance: IPublicClientApplication,
    scopes: Array<string>,
    extraScopesToConsent?: Array<string>,
) => {
    const account = msalInstance.getActiveAccount()!;
    let accessTokenRequest: PopupRequest = {
        scopes: scopes,
        extraScopesToConsent: extraScopesToConsent
    };

    if (account) {
        accessTokenRequest.account = account;
        accessTokenRequest.authority = `https://login.microsoftonline.com/${account.tenantId}`;
    }

    return await acquireToken(accessTokenRequest, msalInstance, inProgress).catch((e) => {
        if (e.message === TokenErrors.InteractionInProgress) {
            return interactionInProgressHandler(inProgress, msalInstance, accessTokenRequest);
        }

        throw e;
    });
};

const acquireToken = async (
    accessTokenRequest: PopupRequest,
    msalInstance: IPublicClientApplication,
    interactionStatus: InteractionStatus,
) => {
    return msalInstance
        .acquireTokenSilent(accessTokenRequest)
        .then(function (accessTokenResponse) {
            // Acquire token silent success
            return accessTokenResponse.accessToken;
        })
        .catch(async (error) => {
            if (error instanceof InteractionRequiredAuthError) {
                // Since app can trigger concurrent interactive requests, first check
                // if any other interaction is in progress proper to invoking a new one
                if (interactionStatus !== InteractionStatus.None) {
                    // throw a new error to be handled in the caller above
                    throw new Error(TokenErrors.InteractionInProgress);
                } else {
                    return msalInstance
                        .acquireTokenPopup({ ...accessTokenRequest })
                        .then(function (accessTokenResponse) {
                            // Acquire token interactive success
                            return accessTokenResponse.accessToken;
                        })
                        .catch(function (error) {
                            // Acquire token interactive failure
                            throw new Error(`Received error while retrieving access token: ${error}`);
                        });
                }
            }
            throw new Error(`Received error while retrieving access token: ${error}`);
        });
};

const interactionInProgressHandler = async (
    interactionStatus: InteractionStatus,
    msalInstance: IPublicClientApplication,
    accessTokenRequest: PopupRequest,
) => {
    // Polls the interaction status from the application
    // state and resolves when it's equal to "None".
    await waitFor(() => interactionStatus === InteractionStatus.None);

    // Wait is over, call acquireToken again to re-try acquireTokenSilent
    return await acquireToken(accessTokenRequest, msalInstance, interactionStatus);
};

const waitFor = (hasInteractionCompleted: () => boolean) => {
    const checkInteraction = (resolve: (arg0: null) => void, _reject: any) => {
        const interactionInProgress = !hasInteractionCompleted();
        while (interactionInProgress) {
            setTimeout(() => {
                hasInteractionCompleted();
            }, 500);
        }
        resolve(null);
    };

    return new Promise(checkInteraction);
};

export const TokenHelper = {
    getAccessTokenUsingMsal,
};

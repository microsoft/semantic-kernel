import { useMsal } from '@azure/msal-react';
import { Constants } from '../../Constants';
import { useAppDispatch } from '../../redux/app/hooks';
import { addAlert } from '../../redux/features/app/appSlice';
import { TokenHelper } from '../auth/TokenHelper';
import { AlertType } from '../models/AlertType';
import { IAsk } from '../semantic-kernel/model/Ask';
import { useSemanticKernel } from '../semantic-kernel/useSemanticKernel';

export const useConnectors = () => {
    const { instance, inProgress } = useMsal();
    const sk = useSemanticKernel(process.env.REACT_APP_BACKEND_URI as string);
    const dispatch = useAppDispatch();

    const makeGraphRequest = async (api: string, scopes: Array<string>, method: string, apiHeaders?: {}) => {
        return await TokenHelper.getAccessToken(inProgress, instance, scopes)
            .then(async (token) => {
                const request = new URL('/v1.0' + api, 'https://graph.microsoft.com');
                return fetch(request, {
                    method: method,
                    headers: {
                        ...apiHeaders,
                        Authorization: `Bearer ${token}`,
                    },
                }).then(async (response) => {
                    if (!response || !response.ok) {
                        throw new Error(`Received error while request ${api}: ${response}`);
                    }
                    return await response.clone().json();
                });
            })
            .catch((e: any) => {
                dispatch(
                    addAlert({
                        type: AlertType.Error,
                        message: e.message ?? (e as string),
                    }),
                );
            });
    };

    /**
     * Helper function to invoke SK skills
     * using custom token header containing
     * access token for downstream connector.
     * scopes should be limited to only permissions needed for the skill
     */
    const invokeSkillWithConnectorToken = async (
        ask: IAsk,
        skillName: string,
        functionName: string,
        scopes: Array<string>,
    ) => {
        return await TokenHelper.getAccessToken(inProgress, instance, scopes).then(async (token: string) => {
            return await sk.invokeAsync(ask, skillName, functionName, token);
        });
    };

    /**
     * Helper function to invoke SK skills
     * using MS Graph API token
     */
    const invokeSkillWithGraphToken = async (ask: IAsk, skillName: string, functionName: string) => {
        return await invokeSkillWithConnectorToken(ask, skillName, functionName, Constants.msGraphScopes);
    };

    /**
     * Helper function to invoke SK skills
     * using ADO token
     */
    const invokeSkillWithAdoToken = async (ask: IAsk, skillName: string, functionName: string) => {
        return await invokeSkillWithConnectorToken(ask, skillName, functionName, Constants.adoScopes);
    };

    return {
        makeGraphRequest,
        invokeSkillWithConnectorToken,
        invokeSkillWithGraphToken,
        invokeSkillWithAdoToken,
    };
};

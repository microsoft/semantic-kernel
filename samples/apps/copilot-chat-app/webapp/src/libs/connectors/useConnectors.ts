import { useMsal } from '@azure/msal-react';
import { Constants } from '../../Constants';
import { useAppSelector } from '../../redux/app/hooks';
import { RootState } from '../../redux/app/store';
import { AuthHeaderTags } from '../../redux/features/plugins/PluginsState';
import { AuthHelper } from '../auth/AuthHelper';
import { TokenHelper } from '../auth/TokenHelper';
import { IAsk } from '../semantic-kernel/model/Ask';
import { SemanticKernelService } from '../services/SemanticKernelService';

export const useConnectors = () => {
    const { instance, inProgress } = useMsal();
    const sk = new SemanticKernelService(process.env.REACT_APP_BACKEND_URI as string);
    const plugins = useAppSelector((state: RootState) => state.plugins);

    /**
     * Helper function to invoke SK skills
     * using custom token header containing
     * Msal access token for downstream plug-ins.
     * scopes should be limited to only permissions needed for the skill
     */
    const invokeSkillWithMsalToken = async (
        ask: IAsk,
        skillName: string,
        functionName: string,
        scopes: Array<string>,
        pluginHeaderTag: AuthHeaderTags,
    ) => {
        return await TokenHelper.getAccessTokenUsingMsal(inProgress, instance, scopes).then(async (token: string) => {
            return await sk.invokeAsync(ask, skillName, functionName, await AuthHelper.getSKaaSAccessToken(instance), [
                {
                    headerTag: pluginHeaderTag,
                    authData: token,
                },
            ]);
        });
    };

    /**
     * Helper function to invoke SK skills
     * using MS Graph API token
     */
    const invokeSkillWithGraphToken = async (ask: IAsk, skillName: string, functionName: string) => {
        return await invokeSkillWithMsalToken(
            ask,
            skillName,
            functionName,
            Constants.msGraphScopes,
            AuthHeaderTags.MsGraph,
        );
    };

    /*
     * Once enabled, each plugin will have a custom dedicated header in every SK request
     * containing respective auth information (i.e., token, encoded client info, etc.)
     * that the server can use to authenticate to the downstream APIs
     */
    const getEnabledPlugins = () => {
        const enabledPlugins: { headerTag: AuthHeaderTags; authData: string; apiProperties?: any }[] = [];

        Object.entries(plugins).map((entry) => {
            const plugin = entry[1];

            if (plugin.enabled) {
                enabledPlugins.push({
                    headerTag: plugin.headerTag,
                    authData: plugin.authData!,
                    apiProperties: plugin.apiProperties,
                });
            }

            return entry;
        });

        return enabledPlugins;
    };

    return {
        invokeSkillWithMsalToken,
        invokeSkillWithGraphToken,
        getEnabledPlugins,
    };
};

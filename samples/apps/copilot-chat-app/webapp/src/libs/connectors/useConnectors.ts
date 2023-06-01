import { useAppSelector } from '../../redux/app/hooks';
import { RootState } from '../../redux/app/store';
import { AuthHeaderTags } from '../../redux/features/plugins/PluginsState';

export const useConnectors = () => {
    const plugins = useAppSelector((state: RootState) => state.plugins);

    /*
     * Once enabled, each plugin will have a custom dedicated header in every Semantic Kernel request
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
        getEnabledPlugins,
    };
};

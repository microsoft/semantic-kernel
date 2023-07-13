import { useAppDispatch } from '../redux/app/hooks';
import { Plugin } from '../redux/features/plugins/PluginsState';
import { addPlugin } from '../redux/features/plugins/pluginsSlice';
import { PluginManifest } from './models/PluginManifest';

export const usePlugins = () => {
    const dispatch = useAppDispatch();

    const addCustomPlugin = (manifest: PluginManifest) => {
        const newPlugin: Plugin = {
            name: manifest.name_for_human,
            publisher: 'Custom Plugin',
            description: manifest.description_for_human,
            enabled: false,
            authRequirements: {
                personalAccessToken: manifest.auth.type === 'user_http',
            },
            headerTag: manifest.name_for_model,
            icon: manifest.logo_url,
        };

        dispatch(addPlugin(newPlugin));
    };

    return {
        addCustomPlugin,
    };
};

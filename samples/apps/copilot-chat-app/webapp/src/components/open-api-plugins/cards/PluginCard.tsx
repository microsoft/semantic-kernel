import { Button } from '@fluentui/react-components';
import { FormEvent } from 'react';
import { useAppDispatch } from '../../../redux/app/hooks';
import { Plugin } from '../../../redux/features/plugins/PluginsState';
import { disconnectPlugin } from '../../../redux/features/plugins/pluginsSlice';
import { PluginConnector } from '../PluginConnector';
import { BaseCard } from './BaseCard';

interface PluginCardProps {
    plugin: Plugin;
}

export const PluginCard: React.FC<PluginCardProps> = ({ plugin }) => {
    const { name, publisher, enabled, authRequirements, apiProperties, icon, description } = plugin;
    const dispatch = useAppDispatch();

    const onDisconnectClick = (event: FormEvent) => {
        event.preventDefault();
        dispatch(disconnectPlugin(name));
    };

    return (
        <BaseCard
            image={icon}
            header={`${name}`}
            secondaryText={publisher}
            description={description}
            action={
                enabled ? (
                    <Button
                        data-testid="disconnectPluginButton"
                        aria-label="Disconnect plugin"
                        appearance="secondary"
                        onClick={onDisconnectClick}
                    >
                        Disable
                    </Button>
                ) : (
                    <PluginConnector
                        name={name}
                        icon={icon}
                        publisher={publisher}
                        authRequirements={authRequirements}
                        apiProperties={apiProperties}
                    />
                )
            }
        />
    );
};

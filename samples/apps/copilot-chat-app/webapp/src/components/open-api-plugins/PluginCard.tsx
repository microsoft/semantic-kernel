import { Button, Caption1, Card, CardHeader, Text, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { FormEvent } from 'react';
import { useAppDispatch } from '../../redux/app/hooks';
import { Plugin } from '../../redux/features/plugins/PluginsState';
import { disconnectPlugin } from '../../redux/features/plugins/pluginsSlice';
import { PluginConnector } from './PluginConnector';

const useStyles = makeStyles({
    main: {
        ...shorthands.gap('36px'),
        display: 'flex',
        flexDirection: 'column',
        flexWrap: 'wrap',
    },
    title: {
        ...shorthands.margin(0, 0, '12px'),
    },
    description: {
        ...shorthands.margin(0, 0, '12px'),
    },
    card: {
        width: '480px',
        maxWidth: '100%',
        height: '124px',
    },
    caption: {
        color: tokens.colorNeutralForeground3,
    },
    logo: {
        ...shorthands.borderRadius('4px'),
        width: '48px',
        height: '48px',
    },
    text: {
        ...shorthands.margin(0),
    },
});

interface PluginCardProps {
    plugin: Plugin;
}

export const PluginCard: React.FC<PluginCardProps> = ({ plugin }) => {
    const { name, publisher, enabled, authRequirements, apiProperties, icon, description } = plugin;

    const styles = useStyles();
    const dispatch = useAppDispatch();

    const onDisconnectClick = (event: FormEvent) => {
        event.preventDefault();
        dispatch(disconnectPlugin(name));
    };

    return (
        <Card className={styles.card}>
            <CardHeader
                image={<img className={styles.logo} src={icon} alt={`Plugin ${name} logo`} />}
                header={<Text weight="semibold">{name}</Text>}
                description={<Caption1 className={styles.caption}>{publisher}</Caption1>}
                action={
                    enabled ? (
                        <Button data-testid="disconnectPluginButton" aria-label="Disconnect plugin" appearance="secondary" onClick={onDisconnectClick}>
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
            <p className={styles.text}>{description}</p>
        </Card>
    );
};

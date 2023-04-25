import { makeStyles, shorthands, tokens } from '@fluentui/react-components';

import { useAppSelector } from '../../redux/app/hooks';
import { RootState } from '../../redux/app/store';
import { BasicAuthPluginButton } from './BasicAuthPluginButton';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        ...shorthands.gap(tokens.spacingHorizontalS),
    },
});

export const PluginsList: React.FC = () => {
    const plugins = useAppSelector((state: RootState) => state.plugins);
    const classes = useClasses();

    return (
        <div className={classes.root}>
            {Object.entries(plugins).map((entry) => {
                const plugin = entry[1];
                const { username, accessToken, helpLink } = plugin.authRequirements;
                return (
                    <BasicAuthPluginButton
                        key={plugin.name}
                        name={plugin.name}
                        icon={plugin.icon}
                        usernameRequired={username}
                        accessTokenRequired={accessToken}
                        enabled={plugin.enabled}
                        helpLink={helpLink}
                    />
                );
            })}
        </div>
    );
};

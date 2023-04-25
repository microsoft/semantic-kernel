import {
    Avatar,
    Body1,
    Button,
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogSurface,
    DialogTitle,
    DialogTrigger,
    Input,
    Label,
    makeStyles,
} from '@fluentui/react-components';
import { FormEvent, useState } from 'react';
import { useAppDispatch } from '../../redux/app/hooks';
import { Plugins } from '../../redux/features/plugins/PluginsState';
import { enablePlugin } from '../../redux/features/plugins/pluginsSlice';

const useStyles = makeStyles({
    content: {
        display: 'flex',
        flexDirection: 'column',
        rowGap: '10px',
    },
});

interface BasicAuthPluginButtonProps {
    name: Plugins;
    icon?: string;
    enabled?: boolean;
    usernameRequired?: boolean;
    passwordRequired?: boolean;
    accessTokenRequired?: boolean;
    helpLink?: string;
    userConsentCallback?: () => {};
}

export const BasicAuthPluginButton: React.FC<BasicAuthPluginButtonProps> = ({
    name,
    icon,
    enabled,
    usernameRequired,
    passwordRequired,
    accessTokenRequired,
    helpLink,
}) => {
    const styles = useStyles();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [accessToken, setAccessToken] = useState('');
    const [open, setOpen] = useState(false);
    const dispatch = useAppDispatch();

    const handleSubmit = (event: FormEvent) => {
        event.preventDefault();
        dispatch(
            enablePlugin({
                plugin: name,
                username: username,
                password: password,
                accessToken: accessToken,
            }),
        );
        setOpen(false);
    };

    // TODO: implement MSAL / OAuth Flows
    // TODO: implement different dialog if enabled
    return (
        <Dialog open={open} onOpenChange={(_event, data) => setOpen(data.open)}>
            <DialogTrigger>
                <Avatar
                    image={{
                        src: icon,
                    }}
                    color="neutral"
                    size={28}
                    name={name}
                    active={enabled ? 'active' : 'inactive'}
                />
            </DialogTrigger>
            <DialogSurface>
                <form onSubmit={handleSubmit}>
                    <DialogBody>
                        <DialogTitle>{`Enable ${name} plug-in?`}</DialogTitle>
                        <DialogContent className={styles.content}>
                            Some additional information is required to enable this plug-in.
                            {usernameRequired && (
                                <>
                                    <Label required htmlFor={'plugin-username-input'}>
                                        Username
                                    </Label>
                                    <Input
                                        required
                                        type="text"
                                        id={'plugin-username-input'}
                                        value={username}
                                        onChange={(_e, input) => {
                                            setUsername(input.value);
                                        }}
                                    />
                                </>
                            )}
                            {passwordRequired && (
                                <>
                                    <Label required htmlFor={'plugin-password-input'}>
                                        Password
                                    </Label>
                                    <Input
                                        required
                                        type="text"
                                        id={'plugin-password-input'}
                                        value={password}
                                        onChange={(_e, input) => {
                                            setPassword(input.value);
                                        }}
                                    />
                                </>
                            )}
                            {accessTokenRequired && (
                                <>
                                    <Label required htmlFor={'plugin-pat-input'} weight="semibold">
                                        Personal Access Token
                                    </Label>
                                    <Body1>
                                        For more information on how to generate a PAT for {name},{' '}
                                        <a href={helpLink} target="_blank" rel="noreferrer noopener">
                                            click here
                                        </a>
                                        .
                                    </Body1>
                                    <Input
                                        required
                                        type="password"
                                        id={'plugin-pat-input'}
                                        value={accessToken}
                                        onChange={(_e, input) => {
                                            setAccessToken(input.value);
                                        }}
                                    />
                                </>
                            )}
                        </DialogContent>
                        <DialogActions>
                            <DialogTrigger>
                                <Button appearance="secondary">Close</Button>
                            </DialogTrigger>
                            <Button type="submit" appearance="primary">
                                Submit
                            </Button>
                        </DialogActions>
                    </DialogBody>
                </form>
            </DialogSurface>
        </Dialog>
    );
};

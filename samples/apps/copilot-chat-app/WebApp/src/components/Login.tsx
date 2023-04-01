// Copyright (c) Microsoft. All rights reserved.

import { InteractionRequiredAuthError } from '@azure/msal-browser';
import { useMsal } from '@azure/msal-react';
import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { Alert } from '@fluentui/react-components/unstable';
import React, { useEffect } from 'react';
import { AuthHelper } from '../libs/AuthHelper';

const useClasses = makeStyles({
    root: {
        ...shorthands.padding(tokens.spacingVerticalM),
    },
});

export const Login: React.FC = () => {
    const classes = useClasses();
    const { instance } = useMsal();
    const [errorMessage, setErrorMessage] = React.useState<string>();

    const handleError = (error: any) => {
        console.error(error);
        setErrorMessage((error as Error).message);
    }

    const handleSignIn = async (): Promise<void> => {
        try {
            await AuthHelper.ssoSilentRequest(instance);
        } catch (error) {
            if (error instanceof InteractionRequiredAuthError) {
                await AuthHelper.loginAsync(instance).catch((error) => {
                    handleError(error);
                });
            }
            handleError(error);
        }
    };

    useEffect(() => {
        handleSignIn();
    }, []);

    return (
        <div className={classes.root}>
            {errorMessage && <Alert intent="error">{errorMessage}</Alert>}
        </div>
    );
};

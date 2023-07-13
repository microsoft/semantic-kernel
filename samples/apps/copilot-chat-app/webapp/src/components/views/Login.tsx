// Copyright (c) Microsoft. All rights reserved.

import { useMsal } from '@azure/msal-react';
import { Body1, Button, Image, Title3 } from '@fluentui/react-components';
import React from 'react';
import signInLogo from '../../ms-symbollockup_signin_light.svg';

export const Login: React.FC = () => {
    const { instance } = useMsal();

    return (
        <div style={{ padding: 40, gap: 10, display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
            <Title3>Login with your Microsoft Account</Title3>
            <Body1>
                {'Don\'t have an account? Create one for free at'}{' '}
                <a href="https://account.microsoft.com/" target="_blank" rel="noreferrer">
                    https://account.microsoft.com/
                </a>
            </Body1>

            <Button style={{ padding: 0 }} appearance="transparent" onClick={() => { instance.loginRedirect().catch(() => { }); }}>
                <Image src={signInLogo} />
            </Button>
        </div>
    );
};

// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogSurface,
    DialogTitle,
    DialogTrigger,
    Divider,
    Switch,
    Tooltip,
    makeStyles,
    shorthands,
} from '@fluentui/react-components';
import { Settings16Regular } from '@fluentui/react-icons';
import React from 'react';

const useClasses = makeStyles({
    root: {
        ...shorthands.overflow('hidden'),
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        height: '100%',
    },
});

export const SettingsDialog: React.FC = () => {
    const classes = useClasses();

    return (
        <Dialog>
            <DialogTrigger disableButtonEnhancement>
                <Tooltip content={'Didnt know how to add this to the menu gracefully'} relationship="label">
                    <Button
                        style={{ color: 'white' }}
                        appearance="transparent"
                        icon={<Settings16Regular color="white" />}
                    ></Button>
                </Tooltip>
            </DialogTrigger>
            <DialogSurface>
                <DialogBody className={classes.root}>
                    <DialogTitle>Settings</DialogTitle>
                    <DialogContent>
                        <h3>Token Usage</h3>
                        <p style={{ display: 'flex' }}>
                            <div style={{ backgroundColor: 'red', height: '10px', width: '20px' }}></div>
                            <div style={{ backgroundColor: 'cyan', height: '10px', width: '40px' }}></div>
                            <div style={{ backgroundColor: 'orange', height: '10px', width: '80px' }}></div>
                            <div style={{ backgroundColor: 'purple', height: '10px', width: '70px' }}></div>
                        </p>
                        <p> Chat (123) | Embeddings (300) | Plans (500) | Plugins (620) </p>
                        <Divider />
                        <h3>Display</h3>
                        <Switch label="Dark Mode" />
                        <Divider />
                        <h3>Plugins & Planners & Personas</h3>
                        <p>The Plans and Persona tab are hidden until you turn this on</p>
                        <Switch label="Activate All" />
                        <Divider />
                        <h3>Azure AI</h3>
                        <Switch label="Azure Content Safety" />
                        <Button>Learn how to activate ACS in code</Button>
                        <Switch disabled label="Azure Cognitive Search" />
                        <Divider />
                        <h3>Experimental</h3>
                        <p>The related icons and menu options are hidden until you turn this on</p>
                        <Switch label="Save/Load Chat Sessions" />
                        <Switch label="Live Chat Session Sharing" />
                        <Divider />
                    </DialogContent>
                    <DialogActions>
                        <DialogTrigger disableButtonEnhancement>
                            <Button appearance="secondary">Close</Button>
                        </DialogTrigger>
                    </DialogActions>
                </DialogBody>
            </DialogSurface>
        </Dialog>
    );
};

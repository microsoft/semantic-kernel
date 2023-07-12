import {
    Button,
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogSurface,
    DialogTitle,
    DialogTrigger,
    Text,
    makeStyles,
    tokens,
} from '@fluentui/react-components';
import { CheckmarkCircle48Regular, Dismiss24Regular } from '@fluentui/react-icons';
import React, { ReactElement, useCallback, useMemo, useState } from 'react';
import { useDialogClasses } from '../styles';
import { EnterManifestStep } from './steps/EnterManifestStep';
import { VerifyManifestStep } from './steps/VerifyManifestStep';

export const useClasses = makeStyles({
    root: {
        zIndex: 5,
        height: '400px',
    },
    center: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        rowGap: tokens.spacingVerticalL,
        'place-self': 'center',
        width: '90%',
    },
});

interface IWizardStep {
    id: CreatePluginSteps;
    header?: string;
    body: ReactElement;
    buttons?: ReactElement;
}

enum CreatePluginSteps {
    EnterManifest,
    VerifyManifest,
    Confirmation,
}

export const PluginWizard: React.FC = () => {
    const classes = useClasses();
    const dialogClasses = useDialogClasses();

    const [activeStep, setActiveStep] = useState(CreatePluginSteps.EnterManifest);
    const [manifestDomain, setManifestDomain] = useState<string | undefined>();
    const [pluginVerified, setPluginVerified] = useState(false);

    const resetLocalState = useCallback(() => {
        setManifestDomain(undefined);
        setActiveStep(CreatePluginSteps.EnterManifest);
        setPluginVerified(false);
    }, []);

    const wizardSteps: IWizardStep[] = useMemo(() => {
        return [
            {
                id: CreatePluginSteps.EnterManifest,
                header: 'Plugin manifest',
                body: <EnterManifestStep manifestDomain={manifestDomain} setManifestDomain={setManifestDomain} />,
                buttons: (
                    <>
                        <DialogTrigger>
                            <Button appearance="secondary">Cancel</Button>
                        </DialogTrigger>
                        <Button
                            data-testid="find-manifest-button"
                            appearance="primary"
                            disabled={!manifestDomain}
                            onClick={() => {
                                setActiveStep(CreatePluginSteps.VerifyManifest);
                            }}
                        >
                            Find manifest file
                        </Button>
                    </>
                ),
            },
            {
                id: CreatePluginSteps.VerifyManifest,
                header: 'Verify Plugin',
                body: (
                    <VerifyManifestStep
                        manifestDomain={manifestDomain}
                        setPluginVerified={() => setPluginVerified(true)}
                    />
                ),
                buttons: (
                    <>
                        <Button
                            data-testid="find-manifest-button"
                            appearance="secondary"
                            onClick={() => {
                                setActiveStep(CreatePluginSteps.EnterManifest);
                            }}
                        >
                            Back
                        </Button>
                        <Button
                            data-testid="find-manifest-button"
                            appearance="primary"
                            disabled={!pluginVerified}
                            onClick={() => {
                                setActiveStep(CreatePluginSteps.Confirmation);
                            }}
                        >
                            Add Plugin
                        </Button>
                    </>
                ),
            },
            {
                id: CreatePluginSteps.Confirmation,
                body: (
                    <div className={classes.center}>
                        <CheckmarkCircle48Regular color="green" />
                        <Text size={600} align="center">
                            Your plugin has been added successfully! Navigate back to the Gallery to enable it.
                        </Text>
                        <DialogTrigger>
                            <Button data-testid="close-plugin-wizard" aria-label="Close Wizard" appearance="secondary">
                                Close
                            </Button>
                        </DialogTrigger>
                    </div>
                ),
            },
        ];
    }, [manifestDomain, pluginVerified, setPluginVerified, classes.center]);

    const currentStep = wizardSteps[activeStep];

    return (
        <Dialog
            onOpenChange={() => {
                resetLocalState();
            }}
            modalType="alert"
        >
            <DialogTrigger>
                <Button data-testid="addCustomPlugin" aria-label="Add Custom Plugin" appearance="primary">
                    Add
                </Button>
            </DialogTrigger>
            <DialogSurface>
                <DialogBody className={classes.root}>
                    <DialogTitle
                        action={
                            <DialogTrigger action="close">
                                <Button
                                    data-testid="closeEnableCCPluginsPopUp"
                                    appearance="subtle"
                                    aria-label="close"
                                    icon={<Dismiss24Regular />}
                                />
                            </DialogTrigger>
                        }
                    >
                        {currentStep.header}
                    </DialogTitle>
                    <DialogContent className={dialogClasses.content}>{currentStep.body}</DialogContent>
                    <DialogActions>{currentStep.buttons}</DialogActions>
                </DialogBody>
            </DialogSurface>
        </Dialog>
    );
};

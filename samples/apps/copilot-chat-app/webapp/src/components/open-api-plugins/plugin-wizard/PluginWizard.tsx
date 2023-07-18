import {
    Button,
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogSurface,
    DialogTitle,
    DialogTrigger,
    Persona,
    Text,
    makeStyles,
    tokens,
} from '@fluentui/react-components';
import { CheckmarkCircle48Regular, Dismiss24Regular } from '@fluentui/react-icons';
import React, { ReactElement, useCallback, useState } from 'react';
import AddPluginIcon from '../../../assets/plugin-icons/add-plugin.png';
import { PluginManifest } from '../../../libs/models/PluginManifest';
import { usePlugins } from '../../../libs/usePlugins';
import { useDialogClasses } from '../../shared/styles';
import { EnterManifestStep } from './steps/EnterManifestStep';
import { VerifyManifestStep } from './steps/VerifyManifestStep';

export const useClasses = makeStyles({
    root: {
        height: '400px',
    },
    surface: {
        width: '450px',
    },
    center: {
        paddingTop: '75px',
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
    header?: ReactElement;
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
    const plugins = usePlugins();

    const [activeStep, setActiveStep] = useState(CreatePluginSteps.EnterManifest);
    const [manifestDomain, setManifestDomain] = useState<string | undefined>();
    const [manifestDomainError, setManifestDomainError] = useState<string | undefined>();
    const [pluginVerified, setPluginVerified] = useState(false);
    const [pluginManifest, setPluginManifest] = useState<PluginManifest | undefined>();

    const resetLocalState = useCallback(() => {
        setManifestDomain(undefined);
        setManifestDomainError(undefined);
        setActiveStep(CreatePluginSteps.EnterManifest);
        setPluginVerified(false);
    }, []);

    const onAddPlugin = useCallback(() => {
        if (pluginManifest && manifestDomain) {
            plugins.addCustomPlugin(pluginManifest, manifestDomain);
            setActiveStep(CreatePluginSteps.Confirmation);
        } else {
            setPluginVerified(false);
            // TODO: add error handling
        }
    }, [pluginManifest, manifestDomain, plugins]);

    const onPluginVerified = useCallback(() => {
        setPluginVerified(true);
    }, []);

    const onManifestVerified = useCallback((manifest: PluginManifest) => {
        setPluginManifest(manifest);
    }, []);

    const setValidManifestDomain = useCallback((domain: string, error?: string) => {
        setManifestDomain(domain);
        setManifestDomainError(error);
    }, []);

    const wizardSteps: IWizardStep[] = [
        {
            id: CreatePluginSteps.EnterManifest,
            header: (
                <Persona
                    size="huge"
                    name="Custom plugin"
                    avatar={{
                        image: {
                            src: AddPluginIcon,
                        },
                        initials: '', // Set to empty string so no initials are rendered behind image
                    }}
                    secondaryText="Connect an OpenAI Plugin to expose Chat Copilot to third-party applications."
                />
            ),
            body: (
                <EnterManifestStep
                    manifestDomain={manifestDomain}
                    manifestDomainError={manifestDomainError}
                    setValidManifestDomain={setValidManifestDomain}
                />
            ),
            buttons: (
                <>
                    <DialogTrigger>
                        <Button appearance="secondary">Cancel</Button>
                    </DialogTrigger>
                    <Button
                        data-testid="find-manifest-button"
                        appearance="primary"
                        disabled={!manifestDomain || manifestDomainError !== undefined}
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
            header: <>Verify Plugin</>,
            body: (
                <VerifyManifestStep
                    manifestDomain={manifestDomain}
                    onPluginVerified={onPluginVerified}
                    pluginManifest={pluginManifest}
                    onManifestVerified={onManifestVerified}
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
                        onClick={onAddPlugin}
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
                    <DialogTrigger disableButtonEnhancement>
                        <Button data-testid="close-plugin-wizard" aria-label="Close Wizard" appearance="secondary">
                            Close
                        </Button>
                    </DialogTrigger>
                </div>
            ),
        },
    ];

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
            <DialogSurface className={classes.surface}>
                <DialogBody className={classes.root}>
                    <DialogTitle
                        action={
                            currentStep.id < CreatePluginSteps.Confirmation ? (
                                <DialogTrigger action="close" disableButtonEnhancement>
                                    <Button
                                        data-testid="closeEnableCCPluginsPopUp"
                                        appearance="subtle"
                                        aria-label="close"
                                        icon={<Dismiss24Regular />}
                                    />
                                </DialogTrigger>
                            ) : undefined
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

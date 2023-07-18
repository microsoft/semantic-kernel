import {
    Body1,
    Body2,
    Input,
    InputOnChangeData,
    Subtitle2,
    Text,
    makeStyles,
    tokens,
} from '@fluentui/react-components';
import { ErrorCircle16Regular } from '@fluentui/react-icons';
import { useCallback, useState } from 'react';

export const useClasses = makeStyles({
    error: {
        display: 'flex',
        color: tokens.colorPaletteRedBorderActive,
        columnGap: tokens.spacingHorizontalS,
        alignItems: 'center',
    },
});

interface IEnterManifestStepProps {
    manifestDomain?: string;
    setValidManifestDomain: (domain: string) => void;
}

export const EnterManifestStep: React.FC<IEnterManifestStepProps> = ({ manifestDomain, setValidManifestDomain }) => {
    const classes = useClasses();

    const [input, setInput] = useState<string>(manifestDomain ?? '');
    const [validationError, setValidationError] = useState<string | undefined>();

    const onInputChange = useCallback(
        (ev: React.ChangeEvent<HTMLInputElement>, data: InputOnChangeData) => {
            ev.preventDefault();
            setInput(data.value);

            try {
                const validUrl = new URL(data.value);
                setValidManifestDomain(validUrl.toString());
                setValidationError(undefined);
            } catch (e) {
                setValidationError('Domain is an invalid URL.');
            }
        },
        [setValidManifestDomain],
    );

    return (
        <>
            <Body2>Connect an OpenAI Plugin to expose Copilot Chat to third-party applications.</Body2>
            <Subtitle2>Enter your website domain</Subtitle2>
            <Text size={400}>
                To connect a plugin, provide the domain of your website where your{' '}
                <a
                    href={'https://platform.openai.com/docs/plugins/getting-started/plugin-manifest'}
                    target="_blank"
                    rel="noreferrer noopener"
                >
                    OpenAI plugin manifest
                </a>{' '}
                is hosted. This is the{' '}
                <Text size={400} weight="bold">
                    ai-plugin.json
                </Text>{' '}
                file.
            </Text>
            <Input
                required
                type="text"
                id={'plugin-domain-input'}
                value={input}
                onChange={onInputChange}
                placeholder={`yourdomain.com`}
            />
            {validationError && (
                <div className={classes.error}>
                    <ErrorCircle16Regular />
                    <Body1>{validationError}</Body1>
                </div>
            )}
            <Body1 italic>
                Note: Copilot Chat currently only supports plugins requiring{' '}
                <a
                    href={'https://platform.openai.com/docs/plugins/authentication/no-authentication'}
                    target="_blank"
                    rel="noreferrer noopener"
                >
                    no auth
                </a>{' '}
                or{' '}
                <a
                    href={'https://platform.openai.com/docs/plugins/authentication/user-level'}
                    target="_blank"
                    rel="noreferrer noopener"
                >
                    user-level
                </a>{' '}
                user-level authentication.
            </Body1>
        </>
    );
};

export default EnterManifestStep;

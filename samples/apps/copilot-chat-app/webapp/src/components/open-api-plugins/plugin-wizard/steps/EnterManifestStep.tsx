import { Body1, Input, InputOnChangeData, Subtitle1, Text, makeStyles, tokens } from '@fluentui/react-components';
import { ErrorCircle16Regular } from '@fluentui/react-icons';
import { useCallback } from 'react';

export const useClasses = makeStyles({
    error: {
        display: 'flex',
        color: tokens.colorPaletteRedBorderActive,
        columnGap: tokens.spacingHorizontalS,
        alignItems: 'center',
    },
    focus: {},
});

interface IEnterManifestStepProps {
    manifestDomain?: string;
    manifestDomainError?: string;
    setValidManifestDomain: (domain: string, error?: string) => void;
}

export const EnterManifestStep: React.FC<IEnterManifestStepProps> = ({
    manifestDomain,
    manifestDomainError,
    setValidManifestDomain,
}) => {
    const classes = useClasses();

    const onInputChange = useCallback(
        (ev: React.ChangeEvent<HTMLInputElement>, data: InputOnChangeData) => {
            ev.preventDefault();
            setValidManifestDomain(data.value);

            // TODO: add debouncing or throttling to avoid excessive validation calls
            try {
                const validUrl = new URL(data.value);
                setValidManifestDomain(validUrl.toString(), undefined);
            } catch (e) {
                setValidManifestDomain(data.value, 'Domain is an invalid URL.');
            }
        },
        [setValidManifestDomain],
    );

    return (
        <>
            <Subtitle1>Enter your website domain</Subtitle1>
            <Text size={400}>
                To connect a plugin, provide the website domain where your{' '}
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
                value={manifestDomain ?? ''}
                onChange={onInputChange}
                placeholder={`yourdomain.com`}
                autoFocus
            />
            {manifestDomainError && (
                <div className={classes.error}>
                    <ErrorCircle16Regular />
                    <Body1>{manifestDomainError}</Body1>
                </div>
            )}
            <Body1 italic>
                Note: Chat Copilot currently only supports plugins requiring{' '}
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

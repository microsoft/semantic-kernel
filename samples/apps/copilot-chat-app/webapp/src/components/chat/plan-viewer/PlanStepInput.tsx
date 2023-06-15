import { Badge, Button, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import { Checkmark16Regular, Dismiss16Regular, Edit16Regular } from '@fluentui/react-icons';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Constants } from '../../../Constants';
import { IPlanInput } from '../../../libs/models/Plan';

const useClasses = makeStyles({
    root: {
        ...shorthands.overflow('hidden'),
        display: 'flex',
    },
    buttons: {
        ...shorthands.padding(tokens.spacingVerticalNone),
        paddingLeft: tokens.spacingHorizontalXXS,
        minWidth: '18px',
    },
    input: {
        ...shorthands.margin(tokens.spacingHorizontalXXS),
        maxHeight: '10px',
        minHeight: '10px',
        fontSize: '12px',
    },
    interactable: {
        zIndex: '50',
    },
});

interface PlanStepInputProps {
    input: IPlanInput;
    onEdit: (newValue: string) => void;
    enableEdits: boolean;
    validationErrors: number;
    setValidationErrors: React.Dispatch<React.SetStateAction<number>>;
}

export const PlanStepInput: React.FC<PlanStepInputProps> = ({
    input,
    onEdit,
    enableEdits,
    validationErrors,
    setValidationErrors,
}) => {
    const classes = useClasses();

    const [formValue, setFormValue] = useState(input.Value);
    const [isEditingInput, setIsEditingInput] = useState(input.Value.includes(Constants.sk.unknownVariableFlag));
    const [inputRequired, setInputRequired] = useState(
        enableEdits && input.Value.includes(Constants.sk.unknownVariableFlag),
    );

    useEffect(() => {
        if (inputRequired) setValidationErrors(validationErrors + 1);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [input.Value]);

    const onEditClick = useCallback(() => {
        setIsEditingInput(true);
    }, []);

    const keyStrokeTimeout = useRef(-1);

    const updateAndValidateInput = useCallback((event: any) => {
        window.clearTimeout(keyStrokeTimeout.current);
        setFormValue(event.target.value);

        // debounce
        keyStrokeTimeout.current = window.setTimeout(() => {
            if (event.target.value.includes(Constants.sk.unknownVariableFlag) || event.target.value === '') {
                setInputRequired(true);
            } else {
                setInputRequired(false);
            }
        }, 250);
    }, []);

    const onSubmitEdit = useCallback(() => {
        if (input.Value.includes(Constants.sk.unknownVariableFlag)) {
            setValidationErrors(validationErrors - 1);
        }

        setInputRequired(false);
        setIsEditingInput(false);
        input.Value = formValue;
        onEdit(formValue);
    }, [formValue, validationErrors, input, onEdit, setValidationErrors]);

    const onCancel = useCallback(() => {
        setIsEditingInput(formValue.includes(Constants.sk.unknownVariableFlag));
        setInputRequired(input.Value.includes(Constants.sk.unknownVariableFlag));
        setFormValue(input.Value);
    }, [input, formValue]);

    return (
        <Badge
            color={enableEdits && input.Value.includes(Constants.sk.unknownVariableFlag) ? 'danger' : 'informative'}
            shape="rounded"
            appearance="tint"
            className={classes.root}
        >
            {`${input.Key}: `}
            {!enableEdits && input.Value}
            {enableEdits && (
                <>
                    {isEditingInput ? (
                        <input
                            className={mergeClasses(classes.input, classes.interactable)}
                            style={{ width: input.Value.length * 6, minWidth: '75px' }}
                            placeholder={input.Value}
                            value={formValue}
                            onChange={updateAndValidateInput}
                            onKeyDown={(event) => {
                                if (event.key === 'Enter' && !event.shiftKey) {
                                    event.preventDefault();
                                    onSubmitEdit();
                                }
                            }}
                        />
                    ) : (
                        formValue
                    )}
                    <Button
                        icon={isEditingInput ? <Checkmark16Regular /> : <Edit16Regular />}
                        appearance="transparent"
                        className={mergeClasses(classes.buttons, classes.interactable)}
                        onClick={isEditingInput ? onSubmitEdit : onEditClick}
                        disabled={isEditingInput && inputRequired}
                    />
                    {isEditingInput && (
                        <Button
                            icon={<Dismiss16Regular />}
                            appearance="transparent"
                            className={mergeClasses(classes.buttons, classes.interactable)}
                            onClick={onCancel}
                        />
                    )}
                </>
            )}
        </Badge>
    );
};

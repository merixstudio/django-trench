import React from 'react';
import {
    Dialog,
    DialogContent,
} from '@material-ui/core';

import { VerificationCodeForm } from './VerificationCodeForm';
import { MethodOnlyForm } from './MethodOnlyForm';




export const ConfirmationDialog = ({
  buttonLabel,
  methods,
  useCode,
  onCancel,
  onSubmit,
}) => (
    <Dialog
        open
        onClose={onCancel}
    >
        <DialogContent>
            {useCode ? (
              <VerificationCodeForm
                methods={methods}
                onSubmit={onSubmit}
                buttonLabel={buttonLabel}
              />
            ):(
              <MethodOnlyForm
                methods={methods}
                onSubmit={onSubmit}
                buttonLabel={buttonLabel}
              />
            )}

        </DialogContent>
    </Dialog>
);

ConfirmationDialog.defaultProps = {
  buttonLabel: 'Confirm',
}



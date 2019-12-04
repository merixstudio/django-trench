import React, { Component } from 'react';
import {
  FormControlLabel,
  FormGroup,
  Switch,
  Paper,
  Radio,
  RadioGroup,
} from '@material-ui/core';

import { VerificationCodeForm } from '../VerificationCodeForm';

export class YubiKeyRequest extends Component {
  render() {
    const {
      activeAuthMethod,
      authBeingActivated,
      verificationPending,
      disabled,
      togglePrimary,
    } = this.props;

    return (
      <div>
        <div style={{ display: 'flex' }}>
          <FormGroup className="method__is-primary">
            <FormControlLabel
              control={
                <RadioGroup
                  name="primary"
                  onChange={togglePrimary}
                  value={(activeAuthMethod && activeAuthMethod.is_primary) ? 'yubi' : ''}
                >
                  <Radio
                    disabled={!activeAuthMethod}
                    value="yubi"
                  />
                </RadioGroup>
              }
            />
          </FormGroup>
          <FormGroup>
            <FormControlLabel
              control={
                <Switch
                  checked={!!activeAuthMethod}
                  onChange={this.props.switchToggle}
                  value="yubi"
                  disabled={disabled}
                />
              }
              label={`${activeAuthMethod ? 'Disable' : 'Enable'} YubiKey Auth`}
            />
          </FormGroup>
        </div>
        {authBeingActivated && verificationPending && (
          <Paper style={{ padding: 16, margin: '20px 0' }}>
            <VerificationCodeForm
              requestResend={this.props.requestRegistration}
              onSubmit={this.props.confirmRegistration}
            />
          </Paper>
        )}
      </div>
    );
  }
}

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

export class EmailRequest extends Component {
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
                  value={(activeAuthMethod && activeAuthMethod.is_primary) ? 'email' : ''}
                >
                  <Radio
                    value="email"
                    disabled={!activeAuthMethod}
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
                  value="email"
                  disabled={disabled}
                />
              }
              label={`${authBeingActivated ? 'Disable' : 'Enable'} Email Auth`}
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

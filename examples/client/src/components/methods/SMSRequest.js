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
import { SMSRequestForm } from '../SMSRequestForm';

export class SMSRequest extends Component {
  render() {
    const {
      activeAuthMethod,
      isEnabled,
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
                  value={(activeAuthMethod && activeAuthMethod.is_primary) ? 'sms' : ''}
                >
                  <Radio
                    disabled={!activeAuthMethod}
                    value="sms"
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
                  value="sms"
                  disabled={disabled}
                />
              }
              label={`${activeAuthMethod ? 'Disable' : 'Enable'} SMS Auth`}
            />
          </FormGroup>
        </div>
        {activeAuthMethod && !verificationPending && !isEnabled && (
          <SMSRequestForm
            onSubmit={this.props.requestRegistration}
            initialValues={{ phone_number: this.props.phoneNumber }}
          />
        )}
        {activeAuthMethod && verificationPending && (
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

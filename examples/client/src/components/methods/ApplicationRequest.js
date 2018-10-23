import React, { Component } from 'react';
import QRCode from 'qrcode.react';
import {
  Typography,
  FormControlLabel,
  FormGroup,
  Switch,
  Paper,
  Radio,
  RadioGroup,
} from '@material-ui/core';

import { VerificationCodeForm } from '../VerificationCodeForm';

export class ApplicationRequest extends Component {
  constructor() {
    super();

    this.state = {
      qrLink: '',
    };

    this.switchToggle = this.switchToggle.bind(this);
  }


  switchToggle(...args) {
    this.props.switchToggle(...args)
      .then((qrLink) => {
        this.setState({
          qrLink: qrLink,
        });
      });
  }

  render() {
    const {
      activeAuthMethod,
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
                  value={(activeAuthMethod && activeAuthMethod.is_primary) ? 'app' : ''}
                >
                  <Radio
                    value="app"
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
                  onChange={this.switchToggle}
                  value="application"
                  disabled={disabled}
                />
              }
              label={`${activeAuthMethod ? 'Disable' : 'Enable'} Application Auth`}
            />
          </FormGroup>
        </div>
        {activeAuthMethod && verificationPending && (
          <div>
            <Typography>
              Scan QR code with your application.
            </Typography>
            {this.state.qrLink && (
              <QRCode
                value={this.state.qrLink}
                size={192}
                style={{margin: '20px auto 0', display: 'block'}}
              />
            )}
            <Paper style={{ padding: 16, margin: '20px 0' }}>
              <VerificationCodeForm
                onSubmit={this.props.confirmRegistration}
              />
            </Paper>
          </div>
        )}
      </div>
    )
  }
}

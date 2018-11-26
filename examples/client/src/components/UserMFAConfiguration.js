import React, { Component } from 'react';

import { Typography } from '@material-ui/core';

import { BackupCodes } from './BackupCodes';
import { ConfirmationDialog } from './ConfirmationDialog';

import {
  request2FAregistration,
  confirm2FAregistration,
  disableFAregistration,
  regenerateBackupCodes,
  requestCodeSend,
  changePrimaryMethod,
} from '../actions';
import { parseError } from '../utils';

import { ApplicationRequest } from './methods/ApplicationRequest';
import { EmailRequest } from './methods/EmailRequest';
import { SMSRequest } from './methods/SMSRequest';
import { YubiKeyRequest } from './methods/YubiKeyRequest';

export class UserMFAConfiguration extends Component {
  constructor() {
    super();

    this.state = {
      enabledAuth: [],
      authBeingActivated: [],
      authWaitingForCode: [],
      codes: [],
      confirmationDialog: null,
    };

    this.toggle2FA = this.toggleField.bind(this, 'twoFAEnabled');

    this.toggleEmailCode = this.toggleField.bind(this, 'email');
    this.toggleSMSCode = this.toggleField.bind(this, 'sms');
    this.toggleYubiKeyAuth = this.toggleField.bind(this, 'yubi');
    this.toggleApplicationAuth = this.toggleField.bind(this, 'app');

    this.requestEmail2FA = this.requestEmail2FA.bind(this);
    this.requestSMS2FA = this.requestSMS2FA.bind(this);
    this.requestYubiKey2FA = this.requestYubiKey2FA.bind(this);
    this.confirm2FAregistration = this.confirm2FAregistration.bind(this);
    this.regenerateBackupCodes = this.regenerateBackupCodes.bind(this);
    this.changePrimaryMethod = this.changePrimaryMethod.bind(this);
  }

  resetRequests(state = {}) {
    this.setState({
      authBeingActivated: [],
      authWaitingForCode: [],
      ...state,
    });
  }

  requestEmail2FA() {
    const { userData } = this.props;

    this.resetRequests({
      authBeingActivated: [{ name: 'email' }],
      authWaitingForCode: ['email'],
    });

    return request2FAregistration({
      method: 'email',
      email: userData.email,
    })
    .then(() => {
      this.props.showMessage('Email has been sent');
    })
    .catch((error) => {
      this.props.showMessage(parseError(error));
      this.resetRequests();
    });
  }

  requestSMS2FA(data = {}) {
    const { userData } = this.props;
    this.resetRequests({
      authBeingActivated: [{ name: 'sms' }],
      authWaitingForCode: ['sms'],
    });

    return this.props.updateUser(data)
      .then(() => {
        return request2FAregistration({
          method: 'sms',
          phone_number: data.phone_number || userData.phone_number,
        });
      })
      .then(() => {
        this.props.showMessage('SMS has been sent');
      }).catch((error) => {
        this.props.showMessage(parseError(error));
        this.resetRequests();
      });
  }

  requestApplication2FA() {
    this.resetRequests({
      authBeingActivated: [{ name: 'app' }],
      authWaitingForCode: ['app'],
    });

    return request2FAregistration({ method: 'app' })
    .catch((error) => {
      this.props.showMessage(parseError(error));
      this.resetRequests();
    });
  }

  requestYubiKey2FA(data = {}) {
    const { userData } = this.props;
    this.resetRequests({
      authBeingActivated: [{ name: 'yubi' }],
      authWaitingForCode: ['yubi'],
    });

    return request2FAregistration({
      method: 'yubi',
      yubikey_id: data.yubikey_id || userData.yubikey_id,
    })
    .catch((error) => {
      this.props.showMessage(parseError(error));
      this.resetRequests();
    });
  }

  confirm2FAregistration({ code }) {
    return confirm2FAregistration({
      method: this.state.authBeingActivated[0].name,
      code,
    }).then(response => {
      this.resetRequests({
        message: '2 factor auth setup correctly',
        codes: response.data.backup_codes || [],
      });
      this.props.getEnabledAuth();
    }).catch((error) => {
      this.props.showMessage(parseError(error));
      this.resetRequests();
    })
  }

  toggleField(method, event) {
    if (event.target.checked) {
      this.setState({
        authBeingActivated: [{ name: method }],
      });
      switch(method) {
        case 'email':
          return this.requestEmail2FA();
        case 'app':
          return this.requestApplication2FA().then(res => res && res.data.qr_link);
        default:
      }
    } else {
      this.remove2FA(method);
    }
    return Promise.resolve();
  }

  createConfirmationDialog(action, methods = null, code = true) {
    return (
      <ConfirmationDialog
        methods={methods}
        useCode={code}
        onSubmit={(data) => console.log(data) || action(data).then(() => this.setState({ confirmationDialog: null }))}
        onCancel={() => this.setState({ confirmationDialog: null })}
      />
    );
  }

  remove2FA(method) {
    const { MFAConfig } = this.props;
    const authToDisable = this.props.enabledAuth.find(auth => auth.name === method);
    const shouldPassNextPrimaryMethod = authToDisable.is_primary && this.props.enabledAuth.length > 2;
    const notPrimaryAuths = this.props.enabledAuth.filter(auth => !auth.is_primary);

    this.resetRequests();
    const action = (data = {}) =>
      disableFAregistration({ ...data, method })
        .then(() => {
          this.props.getEnabledAuth();
        })
        .then(() => {
          this.setState({
            message: 'MFA disabled correctly',
          });
        })
        .catch((error) => {
          this.props.showMessage(parseError(error));
        });

    if (this.props.enabledAuth.find(auth => auth.name === method)) {
      if (MFAConfig.confirm_disable_with_code) {
        requestCodeSend({ method })
        this.setState({
          confirmationDialog: this.createConfirmationDialog(action, shouldPassNextPrimaryMethod && notPrimaryAuths),
        });
      } else if (shouldPassNextPrimaryMethod) {
        this.setState({
          confirmationDialog: this.createConfirmationDialog(action, shouldPassNextPrimaryMethod && notPrimaryAuths, false),
        });
      } else {
        action();
      }
    }
  }

  regenerateBackupCodes() {
    const { MFAConfig } = this.props;
    const method = this.props.enabledAuth.find(auth => auth.is_primary).name;

    this.resetRequests();
    const action = (data) =>
      regenerateBackupCodes({ ...data, method })
        .then((res) => this.setState({ codes: res.data.backup_codes }))
        .catch(error => this.props.showMessage(parseError(error)))

    if (MFAConfig.confirm_regeneration_with_code) {
      requestCodeSend({ method })
      this.setState({
        confirmationDialog: this.createConfirmationDialog(action),
      });
    } else {
      action();
    }
  }

  changePrimaryMethod(event, method) {
    this.resetRequests();
    const action = (data) =>
      changePrimaryMethod({ ...data, method })
        .then((res) => this.props.changeEnabledAuth(res.data))
        .catch(error => this.props.showMessage(parseError(error)))

    requestCodeSend({ method: this.props.enabledAuth.find(auth => auth.is_primary).name })

    this.setState({
      confirmationDialog: this.createConfirmationDialog(action),
    });
  }

  render() {
    const {
      codes,
      authBeingActivated,
      authWaitingForCode,
    } = this.state;
    const {
      userData,
      enabledAuth,
      MFAConfig,
    } = this.props;
    const activeAuthMethod = [...authBeingActivated, ...enabledAuth];

    return (
      <div>
        <Typography>
          Enable any number of application methods
        </Typography>
        <div style={{padding: '0 24px', marginTop: 20 }}>
          <div>
            <Typography>
              Primary
            </Typography>
          </div>
          <EmailRequest
            switchToggle={this.toggleEmailCode}
            togglePrimary={this.changePrimaryMethod}
            requestRegistration={this.requestEmail2FA}
            confirmRegistration={this.confirm2FAregistration}
            activeAuthMethod={activeAuthMethod.find(auth => auth.name === 'email')}
            authBeingActivated={authBeingActivated.find(auth => auth.name === 'email')}
            verificationPending={authWaitingForCode.indexOf('email') !== -1}
            isEnabled={enabledAuth.find(auth => auth.name === 'email')}
          />
          <ApplicationRequest
            switchToggle={this.toggleApplicationAuth}
            togglePrimary={this.changePrimaryMethod}
            requestRegistration={this.requestApplication2FA}
            confirmRegistration={this.confirm2FAregistration}
            activeAuthMethod={activeAuthMethod.find(auth => auth.name === 'app')}
            authBeingActivated={authBeingActivated.find(auth => auth.name === 'app')}
            verificationPending={authWaitingForCode.indexOf('app') !== -1}
            isEnabled={enabledAuth.find(auth => auth.name === 'app')}
          />
          <SMSRequest
            switchToggle={this.toggleSMSCode}
            togglePrimary={this.changePrimaryMethod}
            requestRegistration={this.requestSMS2FA}
            confirmRegistration={this.confirm2FAregistration}
            activeAuthMethod={activeAuthMethod.find(auth => auth.name === 'sms')}
            authBeingActivated={authBeingActivated.find(auth => auth.name === 'sms')}
            verificationPending={authWaitingForCode.indexOf('sms') !== -1}
            isEnabled={enabledAuth.find(auth => auth.name === 'sms')}
            phoneNumber={userData.phone_number}
          />
          <YubiKeyRequest
            switchToggle={this.toggleYubiKeyAuth}
            togglePrimary={this.changePrimaryMethod}
            requestRegistration={this.requestYubiKey2FA}
            confirmRegistration={this.confirm2FAregistration}
            activeAuthMethod={activeAuthMethod.find(auth => auth.name === 'yubi')}
            authBeingActivated={authBeingActivated.find(auth => auth.name === 'yubi')}
            verificationPending={authWaitingForCode.indexOf('yubi') !== -1}
            isEnabled={enabledAuth.find(auth => auth.name === 'yubi')}
            yubikey_id={userData.yubikey_id}
          />
        </div>
        <div>
          <BackupCodes
            codes={!!enabledAuth.length && codes}
            showButton={!!enabledAuth.length && MFAConfig.allow_backup_codes_regeneration}
            regenerateBackupCodes={this.regenerateBackupCodes}
          />
        </div>
        {this.state.confirmationDialog}
      </div>
    );
  }
}

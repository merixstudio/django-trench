import React, { Component } from 'react';
import { withRouter } from 'react-router';
import { Snackbar, Button } from '@material-ui/core';

import { Header } from './Header';
import { UserMFAConfiguration } from './UserMFAConfiguration';
import {
  fetchMe,
  fetchActiveMethods,
  fetchMFAConfig,
  updateMe,
} from '../actions';
import request from '../request';
import HttpsRedirect from 'react-https-redirect';

export class UserDashboardComponent extends Component {
  constructor() {
    super();

    this.state = {
      enabledAuth: [],
      userData: null,
      MFAConfig: {},
      message: '',
    };

    this.updateUser = this.updateUser.bind(this);
    this.getEnabledAuth = this.getEnabledAuth.bind(this);
    this.redirectToLogin = this.redirectToLogin.bind(this);

  }

  componentDidMount() {
    fetchMe()
      .then((res) => {
        this.setState({ userData: res.data });
        this.getEnabledAuth();
        fetchMFAConfig().then((res) => {
          this.setState({ MFAConfig: res.data });
        });
      })
      .catch(() => {
        this.redirectToLogin();
      });
  }

  redirectToLogin() {
    request.clearAuthToken();
        this.props.history.push('/login');
  }

  getEnabledAuth() {
    fetchActiveMethods().then((res) => {
      this.setState({
        enabledAuth: res.data.length > 0 ? res.data : [],
      });
    });
  }

  updateUser(data) {
    const { userData } = this.state;
    if (data.phone_number && userData.phone_number !== data.phone_number) {
      return updateMe(data).then((res) => this.setState({ userData: res.data }));
    } else {
      return Promise.resolve();
    }
  }


  render() {
    const {
      enabledAuth,
      MFAConfig,
      userData,
    } = this.state;

    return (
      <HttpsRedirect>

        <div>
          <Header name="User" />
          <div style={{ padding: '16px 16px 48px' }}>
            <Snackbar
              anchorOrigin={{
                vertical: 'top',
                horizontal: 'center',
              }}
              color="primary"
              open={!!this.state.message}
              autoHideDuration={2000}
              onClose={() => this.setState({ message: '' })}
              message={<span>{this.state.message}</span>}
            />
            {userData && (
              <UserMFAConfiguration
                enabledAuth={enabledAuth}
                userData={userData}
                MFAConfig={MFAConfig}
                showMessage={message => this.setState({ message })}
                changeEnabledAuth={enabledAuth => this.setState({ enabledAuth })}
                getEnabledAuth={this.getEnabledAuth}
                updateUser={this.updateUser}
              />
            )}
            <Button
              variant="contained"
              color="primary"
              onClick={this.redirectToLogin}
              style={{ marginTop: 30 }}
            >
              Logout
            </Button>
          </div>
        </div>
      </HttpsRedirect>
    );
  }
}


export const UserDashboard = withRouter(UserDashboardComponent);

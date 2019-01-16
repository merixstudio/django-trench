import React, { Component } from 'react';
import { withRouter } from 'react-router';
import { Formik } from 'formik';
import * as Yup from 'yup';

import { Header } from './Header';
import { LoginForm } from './LoginForm';
import {
  Typography,
  Snackbar,
} from '@material-ui/core';
import {
  login,
  loginCode,
} from '../actions';

import request from '../request';
import { VerificationCodeForm } from './VerificationCodeForm';
import { parseError } from '../utils';
import HttpsRedirect from 'react-https-redirect';


const validationSchema = Yup.object().shape({
  username: Yup.string()
    .required('Required'),
  password: Yup.string()
    .required('Required'),
});
const initialValues = { username: '', password: '' };

export class LoginComponent extends Component {
  constructor() {
    super();

    this.state = {
      loginError: '',
      method: null,
      ephemeralToken: false,
      otherMethods: [],
      message: '',
    };

    this.loginUser = this.loginUser.bind(this);
    this.loginForm = this.loginForm.bind(this);
    this.loginErrors = this.loginErrors.bind(this);
    this.secondStepLogin = this.secondStepLogin.bind(this);
  }

  loginUser(data) {
    return login(data)
      .then((res) => {
        if (res.data.token) {
          request.setAuthToken(res.data.token);
          this.props.history.push('/');
        } else {
          this.setState({
            ephemeralToken: res.data.ephemeral_token,
            method: res.data.method,
            otherMethods: res.data.other_methods.map(method => method.name),
            message: `Provide the code from ${res.data.method}`,
            loginError: '',
          });
        }
      })
      .catch(this.loginErrors);
  }

  secondStepLogin(data) {
    return loginCode({
      ...data,
      ephemeral_token: this.state.ephemeralToken,
    })
      .then((res) => {
        request.setAuthToken(res.data.token);
        this.setState({ loginError: '' });
        this.props.history.push('/');
      })
      .catch(this.loginErrors);
  }

  loginErrors(error) {
    this.setState({
      loginError: parseError(error),
    });
  }

  loginForm(props) {
    return (
      <LoginForm
        loginError={this.state.loginError}
        {...props}
      />
    );
  }

  render() {
    return (
      <HttpsRedirect>
        <div>
          <Header name="Login" />
          <div
            style={{ padding: '16px 16px 48px', maxWidth: 300, width: '100%', margin: '24px auto 0' }}
          >
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
            {!this.state.ephemeralToken ? (
              <Formik
                initialValues={initialValues}
                validationSchema={validationSchema}
                render={this.loginForm}
                onSubmit={this.loginUser}
              />
            ) : (
              <div>
                <Typography
                  color="error"
                  style={{ marginBottom: 20 }}
                >
                  {this.state.loginError}
                </Typography>
                <VerificationCodeForm
                  method={this.state.method}
                  alternativeMethods={this.state.otherMethods}
                  setMessage={message => this.setState({ message })}
                  onSubmit={this.secondStepLogin}
                />
              </div>
            )}
          </div>
        </div>
      </HttpsRedirect>
    );
  }
}

export const Login = withRouter(LoginComponent);

import React, { Component } from 'react';
import { Formik } from 'formik';
import * as Yup from 'yup';

import { Header } from './Header';
import { RegisterForm } from './RegisterForm';
import HttpsRedirect from 'react-https-redirect';

const validationSchema = Yup.object().shape({
  email: Yup.string()
    .email()
    .required('Required'),
  password: Yup.string()
    .required('Required'),
  confirmPassword: Yup.string()
    .required('Required'),
});
const initialValues = { email: '', password: '', confirmPassword: '' };

export class RegisterComponent extends Component {
  render() {
    return (
        <HttpsRedirect>
          <div>
            <Header name="Register" />
            <Formik
              initialValues={initialValues}
              validationSchema={validationSchema}
              render={RegisterForm}
            />
          </div>
        </HttpsRedirect>
    );
  }
}

export const Register = RegisterComponent;

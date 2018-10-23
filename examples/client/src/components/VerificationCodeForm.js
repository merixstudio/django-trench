import React, { Component } from 'react';
import { withFormik } from 'formik';
import * as Yup from 'yup';
import {
  Button,
  TextField,
  Typography,
  Popover,
  MenuItem,
} from '@material-ui/core';

import { MethodChoice } from './MethodChoice';

const validationSchema = Yup.object().shape({
  code: Yup.string().required('Required'),
});
const initialValues = { code: '' };

class VerificationCodeFormComponent extends Component {
  constructor(props) {
    super();

    this.state = {
      time: 60,
      anchorEl: null,
    };

    this.requestResend = this.requestResend.bind(this);
    this.timeoutFn = this.timeoutFn.bind(this);
    this.useDifferentMethod = this.useDifferentMethod.bind(this);

    this.timeout = setTimeout(this.timeoutFn, 1000);
  }

  timeoutFn() {
    if (this.state.time > 0) {
      this.setState({ time: this.state.time - 1 });
      this.timeout = setTimeout(this.timeoutFn, 1000);
    }
  }

  requestResend() {
    this.props.requestResend();
    this.setState({ time: 60 });
    this.timeout = setTimeout(this.timeoutFn, 1000);
  }

  useDifferentMethod(event) {
    this.props.setMessage(`Provide the code from ${event.target.textContent}`);
    this.setState({ anchorEl: null });
  }

  render() {
    const {
      methods,
      handleSubmit,
      handleChange,
      handleBlur,
      errors,
      touched,
      values,
      setFieldValue,
      alternativeMethods,
      buttonLabel,
    } = this.props;
    const { anchorEl } = this.state;

    return (
      <form onSubmit={handleSubmit}>
        {methods && (
          <MethodChoice
            methods={methods}
            value={values.new_method}
            onChange={value => setFieldValue('new_method', value)}
            error={errors.new_method}
          />
        )}
        <Typography>
          Provide valid code or backup code
        </Typography>
        <TextField
          name="code"
          label="Code"
          fullWidth
          onChange={handleChange}
          onBlur={handleBlur}
          value={values.code}
          error={!!errors.code && touched.code}
          helperText={(touched.code && errors.code) || " "}
        />
        <div style={{ display: 'flex', justifyContent: 'flex-end'}}>
          {this.props.requestResend && (
            <div>
               {this.state.time === 0 ? (
                <Button
                  style={{ marginTop: 20 }}
                  onClick={this.requestResend}
                >
                  Resend Code
                </Button>
              ) : (
                <Button
                  style={{ marginTop: 20 }}
                  disabled
                >
                  {this.state.time} sec
                </Button>
              )}
            </div>
          )}
          <Button
            variant="contained"
            color="primary"
            type="submit"
            style={{ color: '#fff', marginTop: 20 }}
          >
            {buttonLabel}
          </Button>
        </div>
        {alternativeMethods && !!alternativeMethods.length && (
          <div style={{marginTop: 30}}>
            <a
              onClick={event => this.setState({ anchorEl: event.target })}
              className="different-verification-method"
            >
              Use different verification method
            </a>
            <Popover
              open={!!anchorEl}
              anchorEl={anchorEl}
              onClose={() => this.setState({ anchorEl: null })}
              anchorOrigin={{
                vertical: 'bottom',
                horizontal: 'center',
              }}
              transformOrigin={{
                vertical: 'top',
                horizontal: 'center',
              }}

            >
              {anchorEl && alternativeMethods.map(method => (
                <MenuItem
                  key={method}
                  value={method}
                  onClick={this.useDifferentMethod}
                  style={{ width: anchorEl.offsetWidth }}
                >
                  {method}
                </MenuItem>
              ))}
            </Popover>
          </div>
        )}
      </form>
    );
  }
}

export const VerificationCodeForm = withFormik({
  validationSchema,
  validate: (values, props) => {
    const errors = {};
    if (props.methods) {
      if (!values.new_method) {
        errors.new_method = 'Required';
      }
    }
    return errors;
  },
  mapPropsToValues: ({ methods }) => methods ? { ...initialValues, new_method: '' } : initialValues,
  handleSubmit: (values, { props }) => console.log(values) || props.onSubmit(values),
})(VerificationCodeFormComponent);

VerificationCodeForm.defaultProps = {
  onSubmit: () => {},
  buttonLabel: 'Confirm',
};

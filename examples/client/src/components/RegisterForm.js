import React from 'react';
import {
  TextField,
  Button,
} from '@material-ui/core';

export const RegisterForm = ({
  handleSubmit,
  handleChange,
  handleBlur,
  errors,
  touched,
  values,
}) => (
  <form
    onSubmit={handleSubmit}
    style={{ padding: '16px 16px 48px', maxWidth: 300, width: '100%', margin: '24px auto 0' }}
  >
    <div>
      <TextField
        label="Email"
        name="email"
        type="email"
        onChange={handleChange}
        onBlur={handleBlur}
        value={values.email}
        error={!!errors.email && touched.email}
        helperText={errors.email}
        fullWidth
      />
    </div>
    <div>
      <TextField
        label="Password"
        name="password"
        type="password"
        onChange={handleChange}
        onBlur={handleBlur}
        value={values.password}
        error={!!errors.password && touched.password}
        helperText={errors.password}
        fullWidth
      />
    </div>
    <div>
      <TextField
        label="Confirm password"
        name="confirmPassword"
        type="password"
        onChange={handleChange}
        onBlur={handleBlur}
        value={values.confirmPassword}
        error={!!errors.confirmPassword && touched.confirmPassword}
        helperText={errors.confirmPassword}
        fullWidth
      />
    </div>
    <div style={{ display: "flex", justifyContent: "flex-end" }}>
      <Button
        variant="contained"
        color="primary"
        style={{ color: "#FFF", marginTop: 30 }}
        type="submit"
      >
        Register
      </Button>
    </div>
  </form>
);

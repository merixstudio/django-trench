import React from 'react';
import {
  TextField,
  Button,
  Typography,
} from '@material-ui/core';

export const LoginForm = ({
  handleSubmit,
  handleChange,
  handleBlur,
  errors,
  touched,
  values,
  loginError,
}) => {
  return (
    <form
      onSubmit={handleSubmit}
    >
      <Typography
        color="error"
        style={{ marginBottom: 20 }}
      >
        {loginError}
      </Typography>
      <div>
        <TextField
          label="Username"
          name="username"
          onChange={handleChange}
          onBlur={handleBlur}
          error={!!errors.username && touched.username}
          value={values.username}
          helperText={(touched.username && errors.username) || " "}
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
          helperText={(touched.password && errors.password) || " "}
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
          Login
        </Button>
      </div>
    </form>
  );
};

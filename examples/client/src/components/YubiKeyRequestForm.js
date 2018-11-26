import React from 'react';
import {
  TextField,
  Button,
} from '@material-ui/core';
import { withFormik } from 'formik';
import * as Yup from 'yup';

const validationSchema = Yup.object().shape({
  yubikey_id: Yup
    .string()
    .min(12).max(12)
    .required('Required'),
});
const initialValues = { yubikey_id: '' };

const YubiKeyRequestFormComponent = ({
  values,
  handleBlur,
  handleChange,
  handleSubmit,
  touched,
  errors,
}) => (
  <form
    style={{paddingLeft: 24, display: 'flex', alignItems: 'center' }}
    onSubmit={handleSubmit}
>
    <TextField
      label="Yubikey ID"
      name="yubikey_id"
      onChange={handleChange}
      onBlur={handleBlur}
      error={!!errors.yubikey_id && touched.yubikey_id}
      value={values.yubikey_id}
      helperText={(touched.yubikey_id && errors.yubikey_id) || " "}
      fullWidth
    />
    <Button
      variant="outlined"
      color="primary"
      style={{ marginLeft: 30, minWidth: 250, }}
      type="submit"
    >
        Activate
    </Button>
  </form>
);

export const YubiKeyRequestForm = withFormik({
  validationSchema,
  mapPropsToValues: (props) => ({ ...initialValues, ...props.initialValues }),
  handleSubmit: (values, { props }) => props.onSubmit(values),
})(YubiKeyRequestFormComponent);

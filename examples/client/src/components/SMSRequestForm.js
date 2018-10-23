import React from 'react';
import {
  TextField,
  Button,
} from '@material-ui/core';
import { withFormik } from 'formik';
import * as Yup from 'yup';

const validationSchema = Yup.object().shape({
  phone_number: Yup
    .string()
    .matches(
      /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/,
      'Must be valid phonenumber',
    )
    .required('Required'),
});
const initialValues = { phone_number: '' };

const SMSRequestFormComponent = ({
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
      label="Phone number"
      name="phone_number"
      onChange={handleChange}
      onBlur={handleBlur}
      error={!!errors.phone_number && touched.phone_number}
      value={values.phone_number}
      helperText={(touched.phone_number && errors.phone_number) || " "}
      fullWidth
    />
    <Button
      variant="outlined"
      color="primary"
      style={{ marginLeft: 30, minWidth: 250, }}
      type="submit"
    >
      Send verification code
    </Button>
  </form>
)

export const SMSRequestForm = withFormik({
  validationSchema,
  mapPropsToValues: (props) => ({ ...initialValues, ...props.initialValues }),
  handleSubmit: (values, { props }) => props.onSubmit(values),
})(SMSRequestFormComponent);

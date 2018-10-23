import React from 'react';
import { withFormik } from 'formik';
import * as Yup from 'yup';
import { Button } from '@material-ui/core';

import { MethodChoice } from './MethodChoice';


export const MethodOnlyForm = withFormik({
  mapPropsToValues: () => ({ new_method: '' }),
  handleSubmit: (values, { props }) => props.onSubmit(values),
  validationSchema: Yup.object().shape({
    new_method: Yup.string().required('Required'),
  }),
})(({
  buttonLabel,
  methods,
  handleSubmit,
  errors,
  values,
  setFieldValue,
}) => (
  <form onSubmit={handleSubmit}>
    {methods && (
      <MethodChoice
        methods={methods}
        value={values.new_method}
        onChange={value => setFieldValue('new_method', value)}
        error={errors.new_method}
      />
    )}
    <div style={{ display: 'flex', justifyContent: 'flex-end'}}>
      <Button
        variant="contained"
        color="primary"
        type="submit"
        style={{ color: '#fff', marginTop: 20 }}
      >
        {buttonLabel}
      </Button>
    </div>
  </form>
));

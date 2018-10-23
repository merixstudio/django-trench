import React from 'react';
import classnames from 'classnames';
import {
  Typography,
  MenuItem,
} from '@material-ui/core';

export const MethodChoice = ({
  label,
  methods,
  value,
  onChange,
  error,
}) => (
  <div>
    <Typography>
      {label}
    </Typography>
    <ul style={{ padding: 0 }}>
      {methods.map((method) => (
        <MenuItem
          key={method.name}
          onClick={() => onChange(method.name)}
          className={classnames({ 'selected-method': value === method.name })}
        >
          {method.name}
        </MenuItem>
      ))}
    </ul>
    {error && (
      <Typography color="error">
        {error}
      </Typography>
    )}
  </div>
);

MethodChoice.defaultProps = {
  label: 'Choose one of the methods',
};

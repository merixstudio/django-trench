import React from 'react';
import { Paper, Typography } from '@material-ui/core';
import { withTheme } from '@material-ui/core/styles';

export const HeaderComponent = ({ name, theme }) => (
  <Paper
    className="header"
    style={{ backgroundColor: theme.palette.primary.main }}
  >
    <Typography
      style={{ color: "#FFF" }}
      variant="subheading"
    >
      {name}
    </Typography>
  </Paper>
)

export const Header = withTheme()(HeaderComponent);

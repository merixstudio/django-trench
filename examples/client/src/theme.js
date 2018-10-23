import green from '@material-ui/core/colors/green';
import lightGreen from '@material-ui/core/colors/lightGreen';

import { createMuiTheme } from '@material-ui/core/styles';

export const theme = createMuiTheme({
  palette: {
    primary: {
      ...green,
      main: lightGreen[900],
      contrastText: '#ffffff',
    },
  },
});

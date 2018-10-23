import React from 'react';
import ReactDOM from 'react-dom';
import {
  BrowserRouter,
  Route,
  Switch,
} from 'react-router-dom'
import { Paper } from '@material-ui/core';
import { MuiThemeProvider } from '@material-ui/core/styles';

import './index.css';
import { UserDashboard } from './components/UserDashboard';
import { Login } from './components/Login';
import { Register } from './components/Register';
import { theme } from './theme';


ReactDOM.render((
  <BrowserRouter>
      <MuiThemeProvider theme={theme}>
        <Paper className="container">
          <Switch>
            <Route
              exact
              path='/'
              component={UserDashboard}
            />
            <Route
              exact
              path='/login'
              component={Login}
            />
            <Route
              exact
              path='/register'
              component={Register}
            />
          </Switch>
        </Paper>
      </MuiThemeProvider>
  </BrowserRouter>
), document.getElementById('root'));

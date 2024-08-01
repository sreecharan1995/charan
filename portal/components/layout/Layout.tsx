import * as React from 'react';
import { useContext, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/router';
import { styled, useTheme, Theme, CSSObject } from '@mui/material/styles';
import Box from '@mui/material/Box';
import MuiDrawer from '@mui/material/Drawer';
import MuiAppBar, { AppBarProps as MuiAppBarProps } from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import List from '@mui/material/List';
import CssBaseline from '@mui/material/CssBaseline';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import { Button } from '@mui/material';
import Link from 'next/link';
import Image from 'next/image';
import Avatar from '@mui/material/Avatar';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Grid from '@mui/material/Grid';
import SsidChartIcon from '@mui/icons-material/SsidChart';
import BarChartIcon from '@mui/icons-material/BarChart';
import ApiIcon from '@mui/icons-material/Api';
import DriveFileMoveIcon from '@mui/icons-material/DriveFileMove';
import InfoIcon from '@mui/icons-material/Info';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import SettingsIcon from '@mui/icons-material/Settings';
import DriveFileRenameOutlineIcon from '@mui/icons-material/DriveFileRenameOutline';
import { useMsal, useMsalAuthentication } from '@azure/msal-react';
import { AuthenticatedTemplate, UnauthenticatedTemplate } from '@azure/msal-react';
import { AuthenticationResult, InteractionRequiredAuthError, InteractionType } from '@azure/msal-browser';
import SpinVFX from '../../public/SpinVFX.png';
import styles from '../../styles/Main.module.css';
import Breadcrumbs from '../Breadcrumbs';
import { AppContext, SET_USER_PERMISSIONS } from '../../contexts';
import useHttpClient from '../../hooks/useHttpClient';
import { PERMISSIONS_TYPE } from '../../types';

const drawerWidth = 240;

const openedMixin = (theme: Theme): CSSObject => ({
  width: drawerWidth,
  transition: theme.transitions.create('width', {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.enteringScreen,
  }),
  overflowX: 'hidden',
});

const closedMixin = (theme: Theme): CSSObject => ({
  transition: theme.transitions.create('width', {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  overflowX: 'hidden',
  width: `calc(${theme.spacing(7)} + 1px)`,
  [theme.breakpoints.up('sm')]: {
    width: `calc(${theme.spacing(8)} + 1px)`,
  },
});

const DrawerHeader = styled('div')(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'flex-end',
  padding: theme.spacing(0, 1),
  // necessary for content to be below app bar
  ...theme.mixins.toolbar,
}));

interface AppBarProps extends MuiAppBarProps {
  open?: boolean;
}

const AppBar = styled(MuiAppBar, {
  shouldForwardProp: (prop) => prop !== 'open',
})<AppBarProps>(({ theme, open }) => ({
  zIndex: theme.zIndex.drawer + 1,
  transition: theme.transitions.create(['width', 'margin'], {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  ...(open && {
    marginLeft: drawerWidth,
    width: `calc(100% - ${drawerWidth}px)`,
    transition: theme.transitions.create(['width', 'margin'], {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.enteringScreen,
    }),
  }),
}));

const Drawer = styled(MuiDrawer, {
  shouldForwardProp: (prop) => prop !== 'open',
})(({ theme, open }) => ({
  width: drawerWidth,
  flexShrink: 0,
  whiteSpace: 'nowrap',
  boxSizing: 'border-box',
  ...(open && {
    ...openedMixin(theme),
    '& .MuiDrawer-paper': openedMixin(theme),
  }),
  ...(!open && {
    ...closedMixin(theme),
    '& .MuiDrawer-paper': closedMixin(theme),
  }),
}));

function stringToColor(string: string) {
  let hash = 0;
  let i;

  /* eslint-disable no-bitwise */
  for (i = 0; i < string.length; i += 1) {
    hash = string.charCodeAt(i) + ((hash << 5) - hash);
  }

  let color = '#';

  for (i = 0; i < 3; i += 1) {
    const value = (hash >> (i * 8)) & 0xff;
    color += `00${value.toString(16)}`.slice(-2);
  }
  /* eslint-enable no-bitwise */

  return color;
}

function stringAvatar(name: string) {
  if (name.length > 0) {
    return {
      sx: {
        bgcolor: stringToColor(name),
      },
      children: `${name.split(' ')[0][0]}${name.split(' ')[1][0]}`,
    };
  }
}

const menu2 = ['About', 'Privacy Policy', 'Settings'];

export default function Layout({ children }: { children: any }) {
  const theme = useTheme();
  const router = useRouter();
  const httpClient = useHttpClient();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const openUserMenu = Boolean(anchorEl);
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [menu, setMenu] = useState(['Dashboard', 'Analytics', 'SWDS', 'Data Transfer', 'Configs']);
  const { login, result, error } = useMsalAuthentication(InteractionType.Redirect);
  const { accounts, instance } = useMsal();
  const { state, dispatch } = useContext(AppContext);
  const [selectedIndex, setSelectedIndex] = React.useState(0);

  useEffect(() => {
    if (error instanceof InteractionRequiredAuthError) {
      console.log('error InteractionRequiredAuthError', error);
      login(InteractionType.Redirect)
          .then((authenticationResult: AuthenticationResult | null) => {})
          .catch((error) => console.log('login(InteractionType.Redirect) error', error));
    } else if (error) {
      console.log('error', error);
    }
  }, [error, login]);

  useEffect(() => {
    if (accounts.length > 0 && accounts[0].name) {
      setName(accounts[0].name);
    } else {
      setName('');
    }
  }, [accounts]);

  useEffect(() => {
    if (name.length > 0) {
      httpClient
          .get('/api/permissions')
          .then((response: any) => {
            if (response) {
              dispatch({ type: SET_USER_PERMISSIONS, payload: response });

              if (menu && menu.length > 0 && response && response.length > 0) {
                menu.forEach((option: string, index: number) => {
                  if (
                      (option === 'SWDS' && !response.includes(PERMISSIONS_TYPE.SWDS_VIEW_PROFILE)) ||
                      (option === 'Configs' && !response.includes(PERMISSIONS_TYPE.CONFIG_VIEW_CONFIG))
                  ) {
                    menu.splice(index, 1);
                  }
                });
                setMenu(menu);
              } else {
                setMenu(['Dashboard', 'Analytics', 'Data Transfer']);
              }
            }
          })
          .catch((error: Error) => {
            console.log('error', error);
          });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [name]);

  useEffect(() => {
    const pathname = router.pathname.split('/');
    if (pathname.length > 1) {
      const currentMenu = pathname[1];
      let findMenuIndex = menu.findIndex((m) => m.replace(' ', '-').toLowerCase() === currentMenu.toLowerCase());
      if (findMenuIndex < 0) {
        findMenuIndex = menu2.findIndex((m) => m.replace(' ', '-').toLowerCase() === currentMenu.toLowerCase());
        if (findMenuIndex > -1) {
          findMenuIndex = findMenuIndex + 6;
        }
      }
      if (findMenuIndex > -1) {
        setSelectedIndex(findMenuIndex);
      } else {
        setSelectedIndex(0);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [menu, router.pathname]);

  const handleDrawerOpen = () => {
    setOpen(true);
  };

  const handleDrawerClose = () => {
    setOpen(false);
  };

  const handleUserMenuClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setAnchorEl(null);
  };

  const logoutHandler = () => {
    handleUserMenuClose();
    instance.logoutRedirect();
  };

  const handleListItemClick = (event: React.MouseEvent<HTMLDivElement, MouseEvent>, index: number) => {
    setSelectedIndex(index);
  };

  return (
      <Box sx={{ display: 'flex' }}>
        <CssBaseline />
        <UnauthenticatedTemplate>
          <AppBar className={styles.header} position="fixed">
            <Toolbar>
              <Link href={'/'} passHref>
                <a>
                  <Image src={SpinVFX} alt="SpinVFX Logo" width={150} height={37} style={{ cursor: 'pointer' }} />
                </a>
              </Link>
            </Toolbar>
          </AppBar>
          <Box component="main" sx={{ flexGrow: 1, p: 3, marginTop: 12 }}>
            {children}
          </Box>
        </UnauthenticatedTemplate>
        <AuthenticatedTemplate>
          <AppBar className={styles.header} position="fixed" open={open}>
            <Toolbar>
              <IconButton
                  color="inherit"
                  aria-label="open drawer"
                  onClick={handleDrawerOpen}
                  edge="start"
                  sx={{
                    marginRight: 5,
                    ...(open && { display: 'none' }),
                  }}
              >
                <MenuIcon />
              </IconButton>
              <Link href={'/'} passHref>
                <a>
                  <Image src={SpinVFX} alt="SpinVFX Logo" width={150} height={37} style={{ cursor: 'pointer' }} />
                </a>
              </Link>
              <div> {router.pathname.split('/')[1].toUpperCase()} </div>
              <Box sx={{ flexGrow: 1 }} />
              <Box sx={{ flexGrow: 0 }}>
                <Button
                    id="user-button"
                    aria-controls={open ? 'user-menu' : undefined}
                    aria-haspopup="true"
                    aria-expanded={open ? 'true' : undefined}
                    onClick={handleUserMenuClick}
                >
                  <Avatar {...stringAvatar(name)} />
                </Button>
                <Menu
                    id="user-menu"
                    anchorEl={anchorEl}
                    open={openUserMenu}
                    onClose={handleUserMenuClose}
                    MenuListProps={{
                      'aria-labelledby': 'user-button',
                    }}
                >
                  <MenuItem onClick={logoutHandler}>Logout</MenuItem>
                </Menu>
              </Box>
            </Toolbar>
          </AppBar>
          <Drawer variant="permanent" open={open}>
            <DrawerHeader>
              <IconButton onClick={handleDrawerClose}>
                {theme.direction === 'rtl' ? <ChevronRightIcon /> : <ChevronLeftIcon />}
              </IconButton>
            </DrawerHeader>
            <Divider />
            <List>
              {menu.map((text, index) => (
                  <Link key={index} href={'/' + text.toLowerCase().replace(/\s/g, '-')} passHref>
                    <ListItem key={text} disablePadding sx={{ display: 'block' }}>
                      <ListItemButton
                          className={'MenuItem'}
                          onClick={(event) => handleListItemClick(event, index)}
                          selected={selectedIndex === index}
                          sx={{
                            minHeight: 48,
                            justifyContent: open ? 'initial' : 'center',
                            px: 2.5,
                          }}
                      >
                        <ListItemIcon
                            sx={{
                              minWidth: 0,
                              mr: open ? 3 : 'auto',
                              justifyContent: 'center',
                            }}
                        >
                          {text === 'Dashboard' ? (
                              <SsidChartIcon />
                          ) : text === 'Analytics' ? (
                              <BarChartIcon />
                          ) : text === 'SWDS' ? (
                              <ApiIcon />
                          ) : text === 'Data Transfer' ? (
                              <DriveFileMoveIcon />
                          ) : text === 'Configs' ? (
                              <DriveFileRenameOutlineIcon />
                          ) : null}
                        </ListItemIcon>
                        <ListItemText primary={text} sx={{ opacity: open ? 1 : 0 }} />
                      </ListItemButton>
                    </ListItem>
                  </Link>
              ))}
            </List>
            <Divider />
            <List>
              {menu2.map((text, index) => (
                  <Link key={index} href={'/' + text.toLowerCase().replace(/\s/g, '-')} passHref>
                    <ListItem key={text} disablePadding sx={{ display: 'block' }}>
                      <ListItemButton
                          className={'MenuItem'}
                          onClick={(event) => handleListItemClick(event, index + 6)}
                          selected={selectedIndex === index + 6}
                          sx={{
                            minHeight: 48,
                            justifyContent: open ? 'initial' : 'center',
                            px: 2.5,
                          }}
                      >
                        <ListItemIcon
                            sx={{
                              minWidth: 0,
                              mr: open ? 3 : 'auto',
                              justifyContent: 'center',
                            }}
                        >
                          {' '}
                          {index === 0 ? (
                              <InfoIcon />
                          ) : index === 1 ? (
                              <AdminPanelSettingsIcon />
                          ) : index === 2 ? (
                              <SettingsIcon />
                          ) : null}{' '}
                        </ListItemIcon>
                        <ListItemText primary={text} sx={{ opacity: open ? 1 : 0 }} />
                      </ListItemButton>
                    </ListItem>
                  </Link>
              ))}
            </List>
          </Drawer>
          <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
            <DrawerHeader />
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Breadcrumbs />
              </Grid>
              <Grid item xs={12}>
                {children}
              </Grid>
            </Grid>
          </Box>
        </AuthenticatedTemplate>
      </Box>
  );
}
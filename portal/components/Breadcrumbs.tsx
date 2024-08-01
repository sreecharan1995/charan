import * as React from 'react';
import { useContext, useEffect } from 'react';
import Breadcrumbs from '@mui/material/Breadcrumbs';
import Link from '@mui/material/Link';
import { useRouter } from 'next/router';
import { AppContext } from '../contexts';
import {Typography} from "@mui/material";

const breadcrumbMappings: { [index: string]: any } = {
  '/': 'Home',
  '/data-transfer': 'Data Transfer',
  '/dashboard': 'Dashboard',
  '/analytics': 'Analytics',
  '/swds': 'Profiles',
  '/about': 'About',
  '/privacy-policy': 'Privacy policy',
  '/settings': 'Settings',
  '/configs' : 'Configurations', 
};

export default function BasicBreadcrumbs() {
  const [paths, setPaths] = React.useState<string[]>([]);
  const { state: profile, dispatch } = useContext(AppContext);
  const router = useRouter();

  const parsePath = (routerPath: string) => {
    const splitPath = routerPath.split('/');
    let concatPath = '';
    //console.log("routerPath:", routerPath);
    //console.log("splitPath:", splitPath);
    const routePaths = splitPath
      .filter((value) => value.length !== 0 && !value.includes('['))
      .map((path, index) => {
        concatPath = concatPath + '/' + path;
        return concatPath;
      });
    //console.log("routePaths:", routePaths);
    return routePaths.length > 0 ? ['/'].concat(routePaths) : ['/'];
  };

  useEffect(() => {
    const paths = parsePath(router.pathname);
    setPaths(paths);
  }, [router.pathname, profile]);

  return (
    <Breadcrumbs aria-label="breadcrumb">
      {paths.map((link, index, paths) => {
        if (link.includes('edit')) {
          return (
              <Typography key={link}>{profile.name}</Typography>
          );
        } else if(paths.length === index + 1){
          return(
            <Typography key={link}>{
              breadcrumbMappings[link] ? breadcrumbMappings[link] :
              router.pathname.split("/").pop()?.replace(/(?:^|\s)\S/g, function(a) { return a.toUpperCase(); })
            }</Typography>
          );
        }
        return (
          <Link key={link} underline="hover" color="inherit" href={link}>
            {breadcrumbMappings[link]}
          </Link>
        );
      })}
    </Breadcrumbs>
  );
}

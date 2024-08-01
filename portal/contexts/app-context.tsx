import * as React from 'react';
import { useReducer } from 'react';
import { Permission, Permissions } from '../types';

export const SET_SWDS_PROFILE = 'SET_SWDS_PROFILE';
export const GET_SWDS_PROFILE = 'GET_SWDS_PROFILE';
export const SET_USER_PERMISSIONS = 'SET_USER_PERMISSIONS';
export const GET_USER_PERMISSIONS = 'GET_USER_PERMISSIONS';

type Action =
  | { type: typeof SET_SWDS_PROFILE; payload: null }
  | { type: typeof GET_SWDS_PROFILE }
  | { type: typeof SET_USER_PERMISSIONS; payload: null }
  | { type: typeof GET_USER_PERMISSIONS };
type State = {
  name: string | undefined;
  id: string | undefined;
  permissions: Permissions | undefined;
  status: string;
};
type InitialStateType = {
  id: string | undefined;
  name: string | undefined;
  permissions: Permissions | undefined;
  status: string;
};

export const initialState = {
  name: '',
  id: '',
  permissions: [],
  status: '',
};

export function reducer(state: State, action: Action) {
  switch (action.type) {
    case SET_SWDS_PROFILE: {
      return Object.assign({}, state, action.payload);
    }
    case GET_SWDS_PROFILE: {
      return state;
    }
    case SET_USER_PERMISSIONS: {
      return Object.assign({}, state, { permissions: action.payload, status: 'ready' });
    }
    default: {
      throw new Error(`Unhandled action type: ${action}`);
    }
  }
}

export const AppContext = React.createContext<{
  state: InitialStateType;
  dispatch: React.Dispatch<any>;
  isAllowedTo: Function;
  status: string;
}>({
  state: initialState,
  dispatch: () => null,
  isAllowedTo: () => false,
  status: '',
});

export function AppProvider({ children }: any) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const isAllowedTo = (permission: Permission) => {
    // console.log(state);
    return state.permissions?.includes(permission) || false;
  };
  const values = { state, dispatch, isAllowedTo, status: state.status };
  return (
    <>
      <AppContext.Provider value={values}>{children}</AppContext.Provider>
    </>
  );
}

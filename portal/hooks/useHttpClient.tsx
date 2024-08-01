import { useMsal } from '@azure/msal-react';
import { HttpClient } from '../services/HttpClient';

const useHttpClient = () => {
  const { accounts, instance } = useMsal();
  return HttpClient(accounts[0], instance);
};

export default useHttpClient;

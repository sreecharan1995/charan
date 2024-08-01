import { useContext } from 'react';
import { AppContext } from '../contexts/app-context';

const usePermission = () => {
  const { isAllowedTo } = useContext(AppContext);
  return isAllowedTo;
};

export default usePermission;

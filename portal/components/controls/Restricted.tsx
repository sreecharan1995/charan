import React from 'react';
import { Permission } from '../../types';
import usePermission from '../../hooks/usePermission';

type Props = {
  to: Permission;
};

const Restricted: React.FunctionComponent<Props> = ({ to, children }) => {
  const isAllowed = usePermission();

  if (isAllowed(to)) {
    return <>{children}</>;
  }

  return null;
};

export default Restricted;

export type Permission = string;

export type Permissions = Array<Permission>;

export enum PERMISSIONS_TYPE {
  SWDS_VIEW_PROFILE = 'swds_view-profile',
  SWDS_CREATE_PROFILE = 'swds_create-profile',
  SWDS_UPDATE_PROFILE = 'swds_update-profile',
  SWDS_DELETE_PROFILE = 'swds_delete-profile',
  SWDS_VIEW_BUNDLES = 'swds_view-bundles',
  SWDS_CREATE_BUNDLE = 'swds_create-bundle',
  SWDS_UPDATE_BUNDLE = 'swds_update-bundle',
  SWDS_DELETE_BUNDLE = 'swds_delete-bundle',
  SWDS_VIEW_PACKAGES = 'swds_view-packages',
  SWDS_SYNC_TREE_LEVELS = 'swds_sync-tree-levels',
  CONFIG_VIEW_CONFIG = 'configs_view-config',
  CONFIGS_CREATE_CONFIG = 'configs_create-config',
  CONFIGS_UPDATE_CONFIG = 'configs_update-config',
  CONFIG_DELETE_CONFIG = 'configs_delete-config',
}

export enum ActionType {
  EDIT = 'Edit',
  EDIT_BY_IMPORT = 'Update from XML',
  CLONE = 'Clone',
  DELETE = 'Delete',
  CREATE = 'Create',
  IMPORT = 'Import',
  ACTIVE = 'Active',
  DEACTIVATE = 'Deactivate',
  VIEW = 'View',
}

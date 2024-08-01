import React, { useEffect } from 'react';
import { useQuery } from 'react-query';
import { TreeItem, TreeView } from '@mui/lab';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import useHttpClient from '../../hooks/useHttpClient';

interface TreeNode {
  label?: string;
  path: string;
  has_children?: boolean;
  url?: string;
  children?: TreeNode[];
}

const RenderTree = ({ path, nodeIds, onLevelNode, selected, disabled }: any) => {
  const httpClient = useHttpClient();
  const {
    isLoading: levelsIsLoading,
    error: levelsError,
    data: nodes,
  } = useQuery(['levels', path], () => httpClient.get(`/api/levels?path=${path}`), {
    enabled: !!path,
  });

  useEffect(() => {
    if (onLevelNode && !levelsIsLoading && !levelsError && nodes) {
      onLevelNode(nodes);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes]);

  return (
    <>
      {levelsIsLoading ? (
        <div>Loading Levels ...</div>
      ) : levelsError ? (
        <div>An error has occurred for loading Levels</div>
      ) : (
        <TreeItem key={nodes.path} nodeId={nodes.path} label={nodes.label} disabled={disabled}>
          {Boolean(nodes.has_children) && Array.isArray(nodes.children) ? (
            nodes.children.map((node: TreeNode) => {
              if (nodeIds.some((n: any) => n === node.path) || node.path === selected) {
                return (
                  <RenderTree
                    key={node.path}
                    path={node.path}
                    nodeIds={nodeIds}
                    onLevelNode={onLevelNode}
                    selected={selected}
                    disabled={disabled}
                  />
                );
              }
              if (Boolean(node.has_children)) {
                return (
                  <TreeItem key={node.path} nodeId={node.path} label={node.label} disabled={disabled}>
                    <TreeItem nodeId={'grandChildren'} />
                  </TreeItem>
                );
              }
              return <TreeItem key={node.path} nodeId={node.path} label={node.label} disabled={disabled}></TreeItem>;
            })
          ) : Boolean(nodes.has_children) ? (
            <TreeItem nodeId={'children'} disabled={disabled} />
          ) : null}
        </TreeItem>
      )}
    </>
  );
};

const createExpandedNodeIds = (paths: string[]) => {
  let level = '';
  const expandedNodeIds = paths.map((path: string, index: number, array: string[]) => {
    return index === 0 ? '/' : (level = level + '/' + path);
  });
  return expandedNodeIds;
};

export function SiteLevelTreeView(props: any) {
  const httpClient = useHttpClient();
  const { onNodeSelect, defaultSelected, onLevelNode, disabled } = props;
  const expandedNodeIds = createExpandedNodeIds(defaultSelected.split('/'));

  const [selected, setSelected] = React.useState<string>(defaultSelected || '');
  const [nodeIds, setNodeIds] = React.useState<string[]>(expandedNodeIds || []);

  const handleNodeToggle = (event: React.SyntheticEvent, nodeIds: string[]) => {
    // TODO
    setNodeIds(nodeIds);
  };

  const handleNodeFocus = (event: React.SyntheticEvent, value: string) => {
    // TODO
  };

  const handleNodeSelect = async (event: React.SyntheticEvent, nodeId: string) => {
    const alreadySelected = nodeIds.some((n: any) => n === nodeId);
    setSelected(nodeId);
    onNodeSelect(nodeId);
    // this is to handle scenario when a node collapse but represents as a selected node
    if (onLevelNode && alreadySelected) {
      try {
        const response = await httpClient.get(`/api/levels?path=${nodeId}`);
        onLevelNode(response);
      } catch (error) {
        console.log('handleNodeSelect error', error);
      }
    }
  };

  return (
    <TreeView
      aria-label="levels"
      defaultCollapseIcon={<ExpandMoreIcon />}
      defaultExpandIcon={<ChevronRightIcon />}
      onNodeToggle={handleNodeToggle}
      onNodeFocus={handleNodeFocus}
      onNodeSelect={handleNodeSelect}
      selected={selected}
      defaultExpanded={expandedNodeIds}
      disableSelection={disabled}
      sx={{ height: 240, flexGrow: 1, overflowY: 'auto' }}
    >
      {RenderTree({ path: '/', nodeIds, onLevelNode, selected, disabled })}
    </TreeView>
  );
}

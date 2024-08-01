import {
  List,
  ListItem,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextareaAutosize,
} from '@mui/material';
import { Table as MaterialTable } from '@mui/material';
import TablePagination from '@mui/material/TablePagination';
import React from 'react';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import Grid from '@mui/material/Grid';
import Button from '@mui/material/Button';
import axios from 'axios';
import useHttpClient from '../hooks/useHttpClient';

export default function CommentsList(props: any) {
  const { profileId } = props;
  const queryClient = useQueryClient();
  const httpClient = useHttpClient();

  const [page, setPage] = React.useState(0);
  const [rowsPerPage, setRowsPerPage] = React.useState(3);
  const [newComment, setNewComment] = React.useState('');

  const {
    status,
    data: commentsData,
    error: commentsError,
    isFetching,
  } = useQuery(['commentsData', profileId], () => getComments(profileId), { keepPreviousData: true });

  async function getComments(id: string) {
    return await httpClient.get(`/api/profiles/${id}/comments?p=$1&ps=1000`);
  }

  const postProfileComment = async (comment: any) => {
    const response = await httpClient.post(`/api/profiles/${profileId}/comments`, {
      comment: newComment,
      created_by: 'system',
    });
    console.log('postProfileComment', response);
  };

  const { mutate: profileCommentMutate } = useMutation(postProfileComment, {
    onSuccess: async (data) => {
      console.log('useMutation POST profileComment onSuccess', data);
      await queryClient.invalidateQueries('commentsData');
    },
    onError: (error: any) => {
      console.log('useMutation POST profileComment onError', error);
    },
    onSettled: () => {},
  });

  const addComment = async (profileId: string, comment: string) => {
    const data = {
      id: profileId,
      payload: {
        comment: comment,
        created_by: 'system',
      },
    };
    profileCommentMutate(data);
    setNewComment('');
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  function compareCommentsTimestamps(a: any, b: any) {
    if (a.created_at > b.created_at) {
      return -1;
    }
    if (a.created_at < b.created_at) {
      return 1;
    }
    return 0;
  }

  function generateList(commentsList: any) {
    let list = [];

    list = commentsList.items.sort(compareCommentsTimestamps);

    return list;
  }

  return (
    <div>
      {isFetching || status === 'loading' ? (
        <div>Loading...</div>
      ) : commentsError ? (
        <div>An error has occurred</div>
      ) : (
        <>
          <TableContainer>
            <MaterialTable stickyHeader={true}>
              <TableBody>
                {generateList(commentsData)
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((comment: any, index: number) => (
                    <TableRow key={index}>
                      <TableCell>
                        User&nbsp; <b>{comment.created_by}</b>
                        &nbsp;commented at:&nbsp;
                        <b>{comment.created_at}</b>
                        <TextareaAutosize
                          disabled
                          name={'comment'}
                          minRows={2}
                          style={{ width: '100%', padding: 5 }}
                          value={comment.comment}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </MaterialTable>
          </TableContainer>
          {commentsData.items.length !== 0 ? (
            <TablePagination
              rowsPerPageOptions={[3, 5, 10]}
              component="div"
              count={commentsData.items.length}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
            />
          ) : (
            ''
          )}
          <TextareaAutosize
            aria-label="minimum height"
            minRows={4}
            placeholder="Type your comment here"
            style={{ width: '100%', padding: 5 }}
            value={newComment}
            onChange={(event) => setNewComment(event.target.value)}
          />
          <Grid container spacing={2} direction={'row'} justifyContent={'flex-end'}>
            <Grid item>
              <Button variant="contained" size="large" onClick={() => addComment(profileId, newComment)}>
                Add Comment
              </Button>
            </Grid>
          </Grid>
        </>
      )}
    </div>
  );
}

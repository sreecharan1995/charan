import { NextApiResponse } from 'next';

export const errorHandler = (res: NextApiResponse<any>, error: any) => {
  console.log('axios error', JSON.stringify(error));
  if (error.response && error.response.status && error.response.data && error.response.data.detail) {
    res.status(error.response.status).send({ message: error.response.data.detail });
  } else if (error.response && error.response.status) {
    res.status(error.response.status).send({ message: error.message || 'Internal Server Error.' });
  } else {
    res.status(500).send({ message: 'Internal Server Error.' });
  }
};

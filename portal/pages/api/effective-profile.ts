// Next.js API route support: https://nextjs.org/docs/api-routes/introduction
import type { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';
import { errorHandler } from './errorHandler';

export default async function handler(req: NextApiRequest, res: NextApiResponse<any>) {
  let response;
  try {
    if (req.method === 'GET') {
      const { path } = req.query;
      response = await axios
        .get(`${process.env.API_BASEURL_DEPENDENCY_SERVICE}/effective-profile?path=${path}`, {
          headers: { Authorization: req.headers['authorization'] || '' },
        })
        .catch((error) => errorHandler(res, error));
      console.log('/effective-profile GET response', response);
    }
    if (response) {
      res.status(response.status).json(response.data);
    }
  } catch (error) {
    console.log('/effective-profile error:', error);
    if (error && error.response && error.response.status) {
      res.status(error.response.status).send({ message: `${error.message}` });
    } else {
      res.status(500).send({ message: 'Internal Server Error.' });
    }
  }
}

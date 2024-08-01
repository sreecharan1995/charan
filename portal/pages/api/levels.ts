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
        .get(`${process.env.API_BASEURL_LEVELS_SERVICE}/levels?path=${path}`, {
          headers: { Authorization: req.headers['authorization'] || '' },
        })
        .catch((error) => errorHandler(res, error));
      console.log('/levels GET response', response);
    }
    if (response) {
      res.status(response.status).json(response.data);
    }
  } catch (error) {
    console.log('/levels error:', error);
    res.status(500).send('Internal Server Error.');
  }
}

// Next.js API route support: https://nextjs.org/docs/api-routes/introduction
import type { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';
import { errorHandler } from './errorHandler';

export default async function handler(req: NextApiRequest, res: NextApiResponse<any>) {
  let response;
  try {
    if (req.method === 'GET') {
      const { p, ps } = req.query;
      response = await axios
        .get(`${process.env.API_BASEURL_DEPENDENCY_SERVICE}/sites?p=${p}&ps=${ps}`, {
          headers: { Authorization: req.headers['authorization'] || '' },
        })
        .catch((error) => errorHandler(res, error));
      console.log('/sites GET response', response);
    }
    if (response) {
      res.status(response.status).json(response.data);
    }
  } catch (error) {
    console.log('/sites error:', error);
    res.status(500).send('Internal Server Error.');
  }
}

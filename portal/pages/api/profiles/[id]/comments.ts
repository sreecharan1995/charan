// Next.js API route support: https://nextjs.org/docs/api-routes/introduction
import type { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';
import { errorHandler } from '../../errorHandler';

export default async function handler(req: NextApiRequest, res: NextApiResponse<any>) {
  let response;
  const { id, p, ps } = req.query;
  try {
    if (req.method === 'GET') {
      response = await axios
        .get(`${process.env.API_BASEURL_DEPENDENCY_SERVICE}/profiles/${id}/comments?p=1&ps=1000`, {
          headers: { Authorization: req.headers['authorization'] || '' },
        })
        .catch((error) => errorHandler(res, error));
      console.log(`/profiles ${id} GET comments`, response);
    } else if (req.method === 'POST') {
      response = await axios
        .post(`${process.env.API_BASEURL_DEPENDENCY_SERVICE}/profiles/${id}/comments`, req.body, {
          headers: { Authorization: req.headers['authorization'] || '' },
        })
        .catch((error) => errorHandler(res, error));
    }
    if (response) {
      res.status(response.status).json(response.data);
    }
  } catch (error) {
    console.log(`/profiles ${id} bundles error:`, error);
    res.status(500).send({ message: 'Internal Server Error.' });
  }
}

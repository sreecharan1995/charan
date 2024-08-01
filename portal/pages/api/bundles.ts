// Next.js API route support: https://nextjs.org/docs/api-routes/introduction
import type { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';
import { errorHandler } from './errorHandler';

export default async function handler(req: NextApiRequest, res: NextApiResponse<any>) {
  let response;
  try {
    if (req.method === 'POST') {
      const payload = { ...req.body };
      response = await axios
        .post(`${process.env.API_BASEURL_DEPENDENCY_SERVICE}/bundles`, payload, {
          headers: { Authorization: req.headers['authorization'] || '' },
        })
        .catch((error) => errorHandler(res, error));
      console.log('/bundles POST', response);
    } else if (req.method === 'GET') {
      const { p, ps, q, id } = req.query;
      response = await axios
        .get(`${process.env.API_BASEURL_DEPENDENCY_SERVICE}/bundles?p=${p}&ps=${ps}&q=${q}`, {
          headers: { Authorization: req.headers['authorization'] || '' },
        })
        .catch((error) => errorHandler(res, error));
      console.log(`/bundles GET`, response);
    }
    if (response) {
      res.status(response.status).json(response.data);
    }
  } catch (error) {
    console.log(`/bundles GET error:`, error);
    res.status(500).send({ message: 'Internal Server Error.' });
  }
}

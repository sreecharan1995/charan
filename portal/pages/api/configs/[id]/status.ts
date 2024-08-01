// Next.js API route support: https://nextjs.org/docs/api-routes/introduction
import type { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';
import { errorHandler } from '../../errorHandler';

export default async function handler(req: NextApiRequest, res: NextApiResponse<any>) {
  let response;
  const { id } = req.query;
  try {
    if (req.method === 'PUT') {
      response = await axios
        .put(`${process.env.API_BASEURL_CONFIGURATION_SERVICE}/configs/${id}/status`, req.body, {
          headers: { Authorization: req.headers['authorization'] || '' },
        })
        .catch((error) => errorHandler(res, error));
      console.log(`/configs ${id} PUT`, response);
    }
    if (response) {
      if (response.data && response.data.length > 0) {
        res.status(response.status).json(response.data);
      } else {
        console.log('response sending null');
        res.status(response.status).send({});
      }
    }
  } catch (error) {
    console.log(`/configs ${id} error:`, error);
    res.status(500).send({ message: 'Internal Server Error.' });
  }
}

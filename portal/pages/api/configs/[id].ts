// Next.js API route support: https://nextjs.org/docs/api-routes/introduction
import type { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';
import { errorHandler } from '../errorHandler';

export default async function handler(req: NextApiRequest, res: NextApiResponse<any>) {
  let response;
  const { id } = req.query;
  try {
    if (req.method === 'PATCH') {
      response = await axios
        .patch(`${process.env.API_BASEURL_CONFIGURATION_SERVICE}/configs/${id}`, req.body, {
          headers: { Authorization: req.headers['authorization'] || '' },
        })
        .catch((error) => errorHandler(res, error));
      console.log(`/configs ${id} PATCH`, response);
    } else if (req.method === 'DELETE') {
      response = await axios
        .delete(`${process.env.API_BASEURL_CONFIGURATION_SERVICE}/configs/${id}`, {
          headers: { Authorization: req.headers['authorization'] || '' },
        })
        .catch((error) => errorHandler(res, error));
      console.log(`/configs ${id} DELETE`, response);
    } else {
      response = await axios
        .get(`${process.env.API_BASEURL_CONFIGURATION_SERVICE}/configs/${id}/current`, {
          headers: { Authorization: req.headers['authorization'] || '' },
        })
        .catch((error) => errorHandler(res, error));
      console.log(`/configs ${id} GET current`, response);
    }
    if (response) {
      res.status(response.status).json(response.data);
    }
  } catch (error) {
    console.log(`/configs ${id} error:`, error);
    res.status(500).send({ message: 'Internal Server Error.' });
  }
}

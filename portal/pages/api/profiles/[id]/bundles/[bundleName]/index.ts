// Next.js API route support: https://nextjs.org/docs/api-routes/introduction
import type { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';
import { errorHandler } from '../../../../errorHandler';

export default async function handler(req: NextApiRequest, res: NextApiResponse<any>) {
  let response;
  try {
    if (req.method === 'POST') {
      const { id, bundleName } = req.query;
      if (bundleName && bundleName.length > 0) {
        console.log(`/profiles ${id} add to bundle`, bundleName);
        response = await axios
          .post(
            `${process.env.API_BASEURL_DEPENDENCY_SERVICE}/profiles/${id}/bundles/${bundleName}`,
            {},
            { headers: { Authorization: req.headers['authorization'] || '' } }
          )
          .catch((error) => errorHandler(res, error));
        console.log(`/profiles ${id} POST to bundle`, bundleName, response);
      }
    } else if (req.method === 'DELETE') {
      const { id, bundleName } = req.query;
      response = await axios
        .delete(`${process.env.API_BASEURL_DEPENDENCY_SERVICE}/profiles/${id}/bundles/${bundleName}`, {
          headers: { Authorization: req.headers['authorization'] || '' },
        })
        .catch((error) => errorHandler(res, error));
      console.log(`/profiles ${id} DELETE bundle`, bundleName, response);
    }
    if (response) {
      res.status(response.status).json(response.data);
    }
  } catch (error) {
    console.log('/profiles add to bundle error:', error);
    res.status(500).send({ message: 'Internal Server Error.' });
  }
}

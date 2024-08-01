// Next.js API route support: https://nextjs.org/docs/api-routes/introduction
import type { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';
import { errorHandler } from './errorHandler';

export default async function handler(req: NextApiRequest, res: NextApiResponse<any>) {
  let response;
  try {
    if (req.method === 'POST') {
      const payload = { ...req.body };
      const { path } = payload;
      delete payload.path;
      response = await axios
        .post(`${process.env.API_BASEURL_DEPENDENCY_SERVICE}/profiles?path=${path}`, payload, {
          headers: { Authorization: req.headers['authorization'] || '' },
        })
        .catch((error) => errorHandler(res, error));
      console.log('/profiles POST', response);

      // } else if (req.method === 'PATCH') {
      //   const { name } = req.query;
      //   response = await axios
      //     .patch(`${process.env.API_BASEURL_DEPENDENCY_SERVICE}/profiles/${name}`, req.body, {
      //       headers: { Authorization: req.headers['authorization'] || '' },
      //     })
      //     .catch((error) => errorHandler(res, error));
      //   console.log('/profiles PATCH', response);
    } else if (req.method === 'GET') {
      const { p, ps, q, id } = req.query;
      if (id && id.length > 0) {
        response = await axios
          .get(`${process.env.API_BASEURL_DEPENDENCY_SERVICE}/profiles/${id}`, {
            headers: { Authorization: req.headers['authorization'] || '' },
          })
          .catch((error) => errorHandler(res, error));
        console.log('/profiles GET response', response);
      } else {
        response = await axios
          .get(`${process.env.API_BASEURL_DEPENDENCY_SERVICE}/profiles?p=${p}&ps=${ps}&q=${q}`, {
            headers: { Authorization: req.headers['authorization'] || '' },
          })
          .catch((error) => errorHandler(res, error));
        console.log('/profiles GET response', response);
      }
    }
    if (response) {
      res.status(response.status).json(response.data);
    }
  } catch (error) {
    console.log('/profiles error:', error);
    if (error && error.response && error.response.status) {
      res.status(error.response.status).send({ message: `${error.message}` });
    } else {
      res.status(500).send({ message: 'Internal Server Error.' });
    }
  }
}

// Next.js API route support: https://nextjs.org/docs/api-routes/introduction
import type { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';
import { errorHandler } from './errorHandler';

export default async function handler(req: NextApiRequest, res: NextApiResponse<any>) {
  let response;
  try {
    if (req.method === 'POST') {
      const payload = { ...req.body };
      console.log('payload', payload);
      response = await axios
        .post(`${process.env.API_BASEURL_CONFIGURATION_SERVICE}/configs`, payload, {
          headers: { Authorization: req.headers['authorization'] || '' },
        })
        .catch((error) => errorHandler(res, error));
      console.log('/configs POST', response);
      // } else if (req.method === 'PATCH') {
      //   const { id } = req.query;
      //   response = await axios
      //     .patch(`${process.env.API_BASEURL_CONFIGURATION_SERVICE}/configs/${id}`, req.body, {
      //       headers: { Authorization: req.headers['authorization'] || '' },
      //     })
      //     .catch((error) => errorHandler(res, error));
      //   console.log('/configs PATCH', response);
    } else if (req.method === 'GET') {
      const { p, ps, name, id } = req.query;
      if (id && id.length > 0) {
        response = await axios
          .get(`${process.env.API_BASEURL_CONFIGURATION_SERVICE}/configs/${id}`, {
            headers: { Authorization: req.headers['authorization'] || '' },
          })
          .catch((error) => errorHandler(res, error));
        console.log('/configs GET response', response);
      } else {
        // TODO: queryParams workaround, API filters empty name string returned empty config list
        let queryParams;
        if (p) {
          queryParams = `p=${p}`;
        }
        if (ps) {
          queryParams = queryParams ? queryParams + `&ps=${ps}` : `ps=${ps}`;
        }
        if (name) {
          queryParams = queryParams ? queryParams + `&name=${name}` : `name=${name}`;
        }
        response = await axios
          .get(`${process.env.API_BASEURL_CONFIGURATION_SERVICE}/configs?${queryParams}`, {
            headers: { Authorization: req.headers['authorization'] || '' },
          })
          .catch((error) => errorHandler(res, error));
        console.log('/configs GET response', response);
      }
    }
    if (response) {
      res.status(response.status).json(response.data);
    }
  } catch (error) {
    console.log('/configs error:', error);
    if (error && error.response && error.response.status) {
      res.status(error.response.status).send({ message: `${error.message}` });
    } else {
      res.status(500).send({ message: 'Internal Server Error.' });
    }
  }
}

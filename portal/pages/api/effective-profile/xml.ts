// @ts-nocheck TODO: temp
// Next.js API route support: https://nextjs.org/docs/api-routes/introduction
import type { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';
import FormData from 'form-data';
import fs from 'fs';
import multiparty from 'multiparty';
import { errorHandler } from '../errorHandler';

// this is required for parsing multipart/form-data with nextjs
export const config = {
  api: {
    bodyParser: false,
  },
};

export default function handler(req: NextApiRequest, res: NextApiResponse<any>) {
  let response;
  try {
    if (req.method === 'POST' || req.method === 'PUT') {
      const { path } = req.query;
      if (path && path.length > 0) {
        let form = new multiparty.Form();
        form.on('field', function (name, value) {
          console.log(name, value);
        });
        form.on('part', (part) => {
          console.log('part');
        });

        form.parse(req, async (error, fields, files) => {
          const file = Object.keys(files).pop();
          console.log('file is', file);
          console.log('file path', files[file][0].path);

          const formData = new FormData();
          formData.append('file', fs.createReadStream(files[file][0].path), files[file][0].originalFilename);

          if (req.method === 'POST') {
            response = await axios
              .post(`${process.env.API_BASEURL_DEPENDENCY_SERVICE}/effective-profile/xml?path=${path}`, formData, {
                headers: { ...formData.getHeaders(), Authorization: req.headers['authorization'] || '' },
              })
              .catch((error) => errorHandler(res, error));

            console.log('/effective-profile/xml POST', response);
          } else if (req.method === 'PUT') {
            response = await axios
              .put(`${process.env.API_BASEURL_DEPENDENCY_SERVICE}/effective-profile/xml?path=${path}`, formData, {
                headers: { ...formData.getHeaders(), Authorization: req.headers['authorization'] || '' },
              })
              .catch((error) => errorHandler(res, error));

            console.log('/effective-profile/xml PUT', response);
          }

          if (response) {
            res.status(response.status).json(response.data);
          } else {
            res.status(500).send({ message: 'Internal Server Error.' });
          }
        });
      }
    }
  } catch (error) {
    console.log('/effective-profile/xml error:', error);
    res.status(500).send({ message: 'Internal Server Error.' });
  }
}

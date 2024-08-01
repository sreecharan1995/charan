/// Next.js API route support: https://nextjs.org/docs/api-routes/introduction
import type { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';
import { errorHandler } from './errorHandler';

export default async function handler(req: NextApiRequest, res: NextApiResponse<any>) {
  try {
    if (req.method === 'GET') {
      await axios
        .all([
            axios.get(`${process.env.API_BASEURL_DEPENDENCY_SERVICE}/info`),
            axios.get(`${process.env.API_BASEURL_REZ_SERVICE}/info`),
            axios.get(`${process.env.API_BASEURL_LEVELS_SERVICE}/info`),
            axios.get(`${process.env.API_BASEURL_CONFIGURATION_SERVICE}/info`),
            axios.get(`${process.env.API_BASEURL_SOURCING_SERVICE}/info`),
            axios.get(`${process.env.API_BASEURL_SCHEDULER_SERVICE}/info`),
        ])
        .then(
          axios.spread((dep_data, rez_data, level_data, configs_data, sourcing_data, scheduler_data) => {
            res.status(200).json({ dependency_info: dep_data.data, rez_info: rez_data.data,
                level_info: level_data.data, configs_info: configs_data.data, sourcing_info: sourcing_data.data, scheduler_info: scheduler_data.data });
          })
        )
        .catch((error) => errorHandler(res, error));
    }
  } catch (error) {
    console.log('/info error:', error);
    res.status(500).send('Internal Server Error.');
  }
}

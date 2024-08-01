This is a [Next.js](https://nextjs.org/) project bootstrapped with [`create-next-app`](https://github.com/vercel/next.js/tree/canary/packages/create-next-app).

## Getting Started

First:
A file called .env.local must be present in the root of the portal directory.
This file defines the http addresses of all services used by the portal along with some build information not really relevant when developing.
A sample file is provided [here](.env.local.prod).

Second:
Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

We use npm as a wrapper for all Next.js commands. For reference to these see [here](https://nextjs.org/docs/api-reference/cli).

The `pages/api` directory is mapped to `/api/*`. Files in this directory are treated as [API routes](https://nextjs.org/docs/api-routes/introduction) instead of React pages.

## Versions

For library specific versions see [package.json](https://bitbucket.org/spinvfx/spin_microservices/src/develop/portal/package.json)

Node version: Node.js 14.6.0 or newer

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js/) - your feedback and contributions are welcome!


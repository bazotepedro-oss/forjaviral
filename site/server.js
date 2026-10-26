const { createServer } = require('http');
const { parse } = require('url');
const next = require('next');

const dev = process.env.NODE_ENV !== 'production';
const hostname = '0.0.0.0';
const port = parseInt(process.env.PORT || '3000', 10);
const app = next({ dev, hostname, port });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  createServer(async (req, res) => {
    try {
      const parsedUrl = parse(req.url, true);
      await handle(req, res, parsedUrl);
    } catch (err) {
      console.error('Erro na requisição:', req.url, err);
      res.statusCode = 500;
      res.end('Erro interno do servidor');
    }
  }).listen(port, (err) => {
    if (err) throw err;
    console.log(`> Fábrica de Cortes rodando em http://${hostname}:${port}`);
  });
});

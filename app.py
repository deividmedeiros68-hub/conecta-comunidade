"""Conecta Comunidade: demo educativa, Python 3.10+ sem dependências externas."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path
import json, sqlite3, os
from contextlib import contextmanager

ROOT = Path(__file__).parent
DB = ROOT / 'conecta.db'


@contextmanager
def connect():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys = ON')
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def init_db():
    with connect() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS campanhas (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          titulo TEXT NOT NULL CHECK(length(titulo) BETWEEN 3 AND 100),
          descricao TEXT NOT NULL,
          local TEXT NOT NULL,
          data TEXT NOT NULL,
          vagas INTEGER NOT NULL CHECK(vagas BETWEEN 1 AND 10000)
        );
        CREATE TABLE IF NOT EXISTS voluntarios (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          nome TEXT NOT NULL, email TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS inscricoes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          campanha_id INTEGER NOT NULL REFERENCES campanhas(id) ON DELETE CASCADE,
          voluntario_id INTEGER NOT NULL REFERENCES voluntarios(id) ON DELETE CASCADE,
          UNIQUE(campanha_id, voluntario_id)
        );
        ''')


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'static'), **kwargs)

    def respond(self, code, data):
        payload = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(payload)

    def body(self):
        n = int(self.headers.get('Content-Length', '0'))
        if n > 20000: raise ValueError('Conteúdo muito grande')
        obj = json.loads(self.rfile.read(n))
        if not isinstance(obj, dict): raise ValueError('JSON inválido')
        return obj

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/api/campanhas':
            with connect() as c:
                rows = c.execute('''SELECT c.*, COUNT(i.id) inscritos FROM campanhas c
                    LEFT JOIN inscricoes i ON c.id=i.campanha_id GROUP BY c.id ORDER BY c.data, c.id''').fetchall()
            return self.respond(200, [dict(r) for r in rows])
        if path == '/api/indicadores':
            with connect() as c:
                result = {x: c.execute(f'SELECT COUNT(*) FROM {x}').fetchone()[0]
                          for x in ('campanhas', 'voluntarios', 'inscricoes')}
            return self.respond(200, result)
        if path.startswith('/api/'):
            return self.respond(404, {'erro': 'Recurso não encontrado'})
        if path == '/': self.path = '/index.html'
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            data = self.body()
            with connect() as c:
                if path == '/api/campanhas':
                    title = str(data.get('titulo', '')).strip()
                    desc = str(data.get('descricao', '')).strip()
                    place = str(data.get('local', '')).strip()
                    day = str(data.get('data', '')).strip()
                    vagas = int(data.get('vagas', 0))
                    if not (3 <= len(title) <= 100 and desc and place and len(day) == 10 and 1 <= vagas <= 10000):
                        raise ValueError('Preencha corretamente os campos da campanha')
                    cur = c.execute('INSERT INTO campanhas(titulo,descricao,local,data,vagas) VALUES(?,?,?,?,?)',
                                    (title, desc, place, day, vagas))
                    return self.respond(201, {'id': cur.lastrowid})
                if path == '/api/inscricoes':
                    campaign = int(data.get('campanha_id', 0))
                    name = str(data.get('nome', '')).strip()
                    email = str(data.get('email', '')).strip().lower()
                    if len(name) < 2 or len(email) > 200 or '@' not in email:
                        raise ValueError('Nome ou e-mail inválido')
                    row = c.execute('SELECT vagas FROM campanhas WHERE id=?', (campaign,)).fetchone()
                    if not row: return self.respond(404, {'erro': 'Campanha não encontrada'})
                    current = c.execute('SELECT COUNT(*) FROM inscricoes WHERE campanha_id=?', (campaign,)).fetchone()[0]
                    if current >= row['vagas']: return self.respond(409, {'erro': 'Não há mais vagas'})
                    c.execute('INSERT OR IGNORE INTO voluntarios(nome,email) VALUES(?,?)', (name,email))
                    v = c.execute('SELECT id FROM voluntarios WHERE email=?', (email,)).fetchone()['id']
                    c.execute('INSERT INTO inscricoes(campanha_id,voluntario_id) VALUES(?,?)', (campaign,v))
                    return self.respond(201, {'mensagem': 'Inscrição realizada'})
            return self.respond(404, {'erro': 'Recurso não encontrado'})
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            return self.respond(400, {'erro': str(exc)})
        except sqlite3.IntegrityError:
            return self.respond(409, {'erro': 'Inscrição já existente ou dados em conflito'})


if __name__ == '__main__':
    init_db()
    port = int(os.getenv('PORT', '8000'))
    print(f'Conecta Comunidade: http://localhost:{port}')
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()

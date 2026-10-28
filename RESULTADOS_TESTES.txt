"""Testes de integração HTTP usando exclusivamente a biblioteca padrão."""
import importlib.util
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('conecta_app', ROOT / 'app.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        app.DB = Path(cls.tmp.name) / 'test.db'
        app.init_db()
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_address[1]}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)
        cls.tmp.cleanup()

    def request(self, path, obj=None):
        req = Request(self.base+path, data=json.dumps(obj).encode() if obj is not None else None, headers={'Content-Type':'application/json'} if obj is not None else {}, method='POST' if obj is not None else 'GET')
        try:
            with urlopen(req, timeout=3) as res:
                return res.status, json.load(res)
        except HTTPError as ex:
            return ex.code, json.load(ex)

    def test_01_inicio_vazio(self):
        status, data = self.request('/api/indicadores')
        self.assertEqual(status, 200)
        self.assertEqual(data, {'campanhas':0,'voluntarios':0,'inscricoes':0})

    def test_02_cadastro_campanha(self):
        code, data = self.request('/api/campanhas', {'titulo':'Mutirão de limpeza','descricao':'Limpeza de praça','local':'Praça Central','data':'2026-11-20','vagas':1})
        self.assertEqual(code, 201)
        self.assertEqual(data['id'], 1)
        code, campaigns = self.request('/api/campanhas')
        self.assertEqual((code, len(campaigns), campaigns[0]['inscritos']), (200, 1, 0))

    def test_03_inscricao(self):
        code, _ = self.request('/api/inscricoes', {'campanha_id':1, 'nome':'Pessoa Teste','email':'teste@example.org'})
        self.assertEqual(code,201)
        _, stats = self.request('/api/indicadores')
        self.assertEqual(stats, {'campanhas':1,'voluntarios':1,'inscricoes':1})

    def test_04_limite_vagas(self):
        code, _ = self.request('/api/inscricoes', {'campanha_id':1, 'nome':'Pessoa Dois','email':'outro@example.org'})
        self.assertEqual(code,409)

    def test_05_validacao(self):
        code, _ = self.request('/api/campanhas', {'titulo':'X','descricao':'desc','local':'Local','data':'2026-11-20','vagas':0})
        self.assertEqual(code,400)

    def test_06_static(self):
        with urlopen(self.base+'/',timeout=3) as r:
            self.assertEqual(r.status,200)
            self.assertIn(b'Conecta Comunidade',r.read())

if __name__ == '__main__':
    unittest.main(verbosity=2)

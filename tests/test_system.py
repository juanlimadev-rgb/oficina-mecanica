import re
import tempfile
import unittest
from pathlib import Path

from app import create_app
from models import db, Usuario


class SystemTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="oficina-teste-")
        self.app = create_app({
            "TESTING": True, "SECRET_KEY": "chave-apenas-de-teste",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(Path(self.directory.name) / "teste.db"),
            "PDF_DIR": str(Path(self.directory.name) / "pdfs"),
        })
        self.client = self.app.test_client()
        result = self.app.test_cli_runner().invoke(args=[
            "create-user", "--name", "Pessoa Teste", "--username", "teste",
            "--password", "senha-ficticia-de-teste",
        ])
        self.assertEqual(result.exit_code, 0, result.output)
        self.token = self.csrf()
        response = self.client.post("/login", data={"usuario": "teste", "senha": "senha-ficticia-de-teste", "csrf_token": self.token})
        self.assertEqual(response.status_code, 302)
        self.token = self.csrf("/clientes")

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        self.directory.cleanup()

    def csrf(self, url="/login"):
        html = self.client.get(url).get_data(as_text=True)
        return re.search(r'name="csrf-token" content="([^"]+)"', html).group(1)

    def api(self, method, url, body=None):
        return self.client.open(url, method=method, json=body, headers={"X-CSRF-Token": self.token})

    def customer(self, **fields):
        response = self.api("POST", "/api/clientes", {"nome": "Cliente Fictício", **fields})
        self.assertEqual(response.status_code, 201, response.get_data(as_text=True))
        return response.json

    def order(self, customer_id, **fields):
        return self.api("POST", "/api/ordens", {"cliente_id": customer_id,
            "itens": [{"descricao": "Revisão", "quantidade": 2, "valor_unitario": 35.25}], **fields})

    def test_unauthenticated_routes(self):
        guest = self.app.test_client()
        for url in ("/api/clientes", "/api/ordens", "/api/faturamento", "/api/faturamento/por-mes", "/api/financeiro", "/api/ordens/1/pdf"):
            self.assertEqual(guest.get(url).status_code, 401, url)
        for url in ("/", "/clientes", "/historico", "/nova-os", "/editar-os/1", "/dashboard", "/financeiro", "/cadastro"):
            self.assertEqual(guest.get(url).status_code, 302, url)

    def test_csrf_and_bad_login(self):
        self.assertEqual(self.client.post("/api/clientes", json={"nome": "Bloqueado"}).status_code, 400)
        guest = self.app.test_client()
        html = guest.get("/login").get_data(as_text=True)
        token = re.search(r'name="csrf-token" content="([^"]+)"', html).group(1)
        self.assertEqual(guest.post("/login", data={"usuario": "teste", "senha": "errada", "csrf_token": token}).status_code, 302)
        self.assertEqual(guest.get("/api/clientes").status_code, 401)

    def test_missing_favicon_does_not_invalidate_login_form(self):
        guest = self.app.test_client()
        html = guest.get("/login").get_data(as_text=True)
        token = re.search(r'name="csrf-token" content="([^"]+)"', html).group(1)
        self.assertEqual(guest.get("/favicon.ico").status_code, 404)
        self.assertEqual(guest.get("/api/clientes").status_code, 401)
        response = guest.post("/login", data={"usuario": "teste", "senha": "senha-ficticia-de-teste", "csrf_token": token})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(guest.get("/api/clientes").status_code, 200)

    def test_logout_and_user_registration(self):
        self.assertEqual(self.client.post("/cadastro", data={"nome": "Segundo", "usuario": "segundo", "senha": "senha-de-teste", "csrf_token": self.token}).status_code, 302)
        self.assertEqual(self.client.post("/logout", data={"csrf_token": self.token}).status_code, 302)
        self.assertEqual(self.client.get("/api/clientes").status_code, 401)
        self.assertEqual(self.client.post("/cadastro", data={"nome": "Bloqueado"}).status_code, 302)

    def test_pages_render_and_local_assets(self):
        for url in ("/", "/clientes", "/nova-os", "/historico", "/dashboard", "/financeiro", "/cadastro"):
            self.assertEqual(self.client.get(url).status_code, 200, url)
        for name in ("app.js", "security.js", "style.css", "logo.png"):
            response = self.client.get("/static/" + name)
            self.assertEqual(response.status_code, 200)
            response.close()

    def test_optional_unique_fields_and_normalization(self):
        self.customer()
        self.customer(nome="Outro Cliente")
        first = self.customer(telefone="(79) 90000-0000", placa="abc-1d23")
        self.assertEqual(first["telefone"], "79900000000")
        self.assertEqual(first["placa"], "ABC1D23")
        for fields in ({"telefone": "79900000000"}, {"placa": "abc1d23"}):
            self.assertEqual(self.api("POST", "/api/clientes", {"nome": "Duplicado", **fields}).status_code, 400)

    def test_empty_names_and_invalid_json(self):
        for body in ({"nome": "  "}, {"nome": None}, [], "texto"):
            self.assertEqual(self.api("POST", "/api/clientes", body).status_code, 400)
        for body in ([], "texto", {"cliente_id": "inválido"}):
            self.assertEqual(self.api("POST", "/api/ordens", body).status_code, 400)

    def test_customer_edit_search_delete(self):
        customer = self.customer()
        path = f'/api/clientes/{customer["id"]}'
        self.assertEqual(self.api("PUT", path, {"nome": "Nome Atualizado"}).status_code, 200)
        self.assertEqual(len(self.client.get("/api/clientes?busca=Atualizado").json), 1)
        self.assertEqual(self.api("DELETE", path).status_code, 200)
        self.assertEqual(self.client.get(path).status_code, 404)

    def test_order_edit_preserves_total_and_revenue_rules(self):
        customer = self.customer()
        pending = self.order(customer["id"], status="pendente")
        self.assertEqual(pending.status_code, 201)
        path = f'/api/ordens/{pending.json["id"]}'
        self.assertEqual(pending.json["valor_total"], 70.5)
        self.assertEqual(self.client.get("/api/faturamento").json["faturamento_total"], 0)
        edited = self.api("PUT", path, {"status": "finalizada", "itens": [{"descricao": "Óleo", "quantidade": 3, "valor_unitario": 10.1}]})
        self.assertEqual(edited.json["valor_total"], 30.3)
        self.assertEqual(len(edited.json["itens"]), 1)
        self.assertEqual(self.client.get("/api/faturamento").json["faturamento_total"], 30.3)
        self.assertEqual(len(self.client.get("/api/financeiro").json), 1)
        self.api("PUT", path, {"status": "cancelada"})
        self.assertEqual(self.client.get("/api/faturamento").json["faturamento_total"], 0)
        self.assertEqual(self.api("DELETE", path).status_code, 200)
        self.assertEqual(self.client.get(path).status_code, 404)

    def test_invalid_order_does_not_destroy_existing_items(self):
        order = self.order(self.customer()["id"]).json
        path = f'/api/ordens/{order["id"]}'
        for items in ([], [{"descricao": "x", "quantidade": -1}], [{"descricao": "x", "valor_unitario": "errado"}], [{"descricao": "x", "valor_unitario": "NaN"}], [{"descricao": ""}]):
            self.assertEqual(self.api("PUT", path, {"itens": items}).status_code, 400)
            self.assertEqual(self.client.get(path).json["valor_total"], 70.5)
        self.assertEqual(self.order(order["cliente_id"], status="inexistente").status_code, 400)
        self.assertEqual(self.order(order["cliente_id"], data="inválida").status_code, 400)

    def test_date_filters_and_monthly_revenue(self):
        customer = self.customer()
        self.order(customer["id"], data="2026-01-20")
        self.order(customer["id"], data="2026-02-20", status="pendente")
        self.assertEqual(len(self.client.get("/api/ordens?data_inicio=2026-01-01&data_fim=2026-01-31").json), 1)
        revenue = self.client.get("/api/faturamento?data_inicio=2026-01-01&data_fim=2026-01-31").json
        self.assertEqual(revenue["faturamento_periodo"], 70.5)
        self.assertEqual(self.client.get("/api/faturamento/por-mes").json, [{"mes": "2026-01", "quantidade": 1, "total": 70.5}])
        for url in ("/api/ordens?cliente_id=erro", "/api/ordens?data_inicio=erro", "/api/financeiro?data_fim=erro"):
            self.assertEqual(self.client.get(url).status_code, 400)

    def test_pdf_and_safe_filename(self):
        order = self.order(self.customer(nome="Cliente / Teste")["id"]).json
        response = self.client.get(f'/api/ordens/{order["id"]}/pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertTrue(response.data.startswith(b"%PDF-"))
        self.assertTrue((Path(self.directory.name) / "pdfs" / f'OS_{order["id"]}.pdf').exists())
        response.close()

    def test_persistence_after_restarting_app(self):
        customer = self.customer()
        self.order(customer["id"])
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        restarted = create_app({key: self.app.config[key] for key in ("TESTING", "SECRET_KEY", "SQLALCHEMY_DATABASE_URI", "PDF_DIR")})
        with restarted.app_context():
            self.assertEqual(db.session.get(Usuario, 1).usuario, "teste")
            from models import Cliente, OrdemServico
            self.assertEqual(Cliente.query.count(), 1)
            self.assertEqual(OrdemServico.query.first().valor_total, 70.5)
            db.session.remove()
            db.engine.dispose()


if __name__ == "__main__":
    unittest.main()

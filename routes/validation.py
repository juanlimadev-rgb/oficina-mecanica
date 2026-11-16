"""Validação de entradas antes de alterar os modelos existentes."""
from datetime import datetime
from math import isfinite

STATUSES = {"pendente", "finalizada", "cancelada"}


def validate_order(data):
    if not isinstance(data, dict):
        raise ValueError("Informe um objeto JSON.")
    for field in ("descricao", "forma_pagamento"):
        if field in data and data[field] is not None and not isinstance(data[field], str):
            raise ValueError("Descrição e forma de pagamento devem ser textos.")
    if "status" in data and (not isinstance(data["status"], str) or data["status"] not in STATUSES):
        raise ValueError("Status inválido.")
    if data.get("data"):
        try:
            datetime.strptime(data["data"], "%Y-%m-%d")
        except (ValueError, TypeError):
            raise ValueError("Data inválida.") from None
    if "itens" in data:
        if not isinstance(data["itens"], list) or not data["itens"]:
            raise ValueError("Adicione pelo menos um item.")
        total = 0
        for item in data["itens"]:
            if not isinstance(item, dict) or not isinstance(item.get("descricao"), str) or not item["descricao"].strip():
                raise ValueError("Descrição do item é obrigatória.")
            try:
                quantity = float(item.get("quantidade", 1))
                value = float(item.get("valor_unitario", 0))
            except (ValueError, TypeError):
                raise ValueError("Quantidade e valor devem ser números.") from None
            if not isfinite(quantity) or not isfinite(value) or quantity <= 0 or value < 0:
                raise ValueError("Quantidade deve ser positiva e valor não pode ser negativo.")
            total += quantity * value
        if not isfinite(total):
            raise ValueError("Total inválido.")

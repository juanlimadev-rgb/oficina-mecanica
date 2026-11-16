# ============================================================
# CONFIGURAÇÃO DO BANCO DE DADOS
# ============================================================
#
# Por padrão, o sistema usa SQLite (arquivo instance/oficina.db criado
# automaticamente na pasta de dados locais). Não precisa configurar nada
# para rodar assim.
#
# Se você já tem um banco MySQL criado e quer usar ele,
# defina USE_MYSQL = True e preencha os dados de conexão abaixo.
#
# Requisitos para usar MySQL:
#   pip install pymysql
#
# O banco MySQL precisa já existir (CREATE DATABASE oficina;)
# As tabelas são criadas automaticamente pelo sistema na primeira execução.
# ============================================================

USE_MYSQL = False

MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "oficina",
}

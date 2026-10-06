-- ============================================================
-- Script de setup inicial do banco de dados
-- Execute este arquivo UMA VEZ no pgAdmin antes de rodar o ETL
-- ============================================================

-- PASSO 1: Execute conectado ao banco "postgres" (padrão)
-- Descomente a linha abaixo apenas se o banco ainda não existir:
-- CREATE DATABASE projeto_bi;

-- PASSO 2: Conecte ao banco "projeto_bi" e execute o restante:

-- Cria o schema que vai receber o Data Warehouse (Camada Gold)
CREATE SCHEMA IF NOT EXISTS dw;

-- Verificação: lista os schemas existentes
SELECT schema_name FROM information_schema.schemata;

-- Registra quando e qual versão dos Termos de Uso / Política de Privacidade foi aceita (LGPD).
-- Rodar uma vez em cada banco (local e produção) antes de subir a versão nova do app.py.

ALTER TABLE usuarios
    ADD COLUMN termos_aceitos_em DATETIME NULL AFTER termos_aceitos,
    ADD COLUMN termos_versao VARCHAR(30) NULL AFTER termos_aceitos_em;

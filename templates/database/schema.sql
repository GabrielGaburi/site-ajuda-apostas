CREATE DATABASE IF NOT EXISTS plataforma_apostas
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE plataforma_apostas;


-- =========================================
-- USUÁRIOS
-- =========================================

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,

    nome VARCHAR(100) NOT NULL,
    sobrenome VARCHAR(100) NOT NULL,

    cpf VARCHAR(14) NOT NULL UNIQUE,

    data_nascimento DATE NOT NULL,

    sexo VARCHAR(30),

    email VARCHAR(150) NOT NULL UNIQUE,

    telefone VARCHAR(20),

    cep VARCHAR(9),
    estado VARCHAR(2),
    cidade VARCHAR(100),
    rua VARCHAR(150),
    numero VARCHAR(20),
    bairro VARCHAR(100),

    senha_hash VARCHAR(255) NOT NULL,

    tipo ENUM('usuario', 'profissional', 'admin')
        NOT NULL DEFAULT 'usuario',

    status ENUM('ativo', 'banido')
        NOT NULL DEFAULT 'ativo',

    email_confirmado BOOLEAN
        NOT NULL DEFAULT FALSE,

    termos_aceitos BOOLEAN
        NOT NULL DEFAULT FALSE,

    data_cadastro TIMESTAMP
        DEFAULT CURRENT_TIMESTAMP
);


-- =========================================
-- PROFISSIONAIS
-- =========================================

CREATE TABLE profissionais (
    id INT AUTO_INCREMENT PRIMARY KEY,

    usuario_id INT NOT NULL,

    crp VARCHAR(20) NOT NULL UNIQUE,
    uf_crp VARCHAR(2) NOT NULL,

    experiencia INT NOT NULL,

    especialidade VARCHAR(100) NOT NULL,

    faculdade VARCHAR(150) NOT NULL,

    pos VARCHAR(150) NOT NULL,

    biografia TEXT,

    foto VARCHAR(255),

    status_aprovacao ENUM(
        'pendente',
        'aprovado',
        'recusado'
    ) NOT NULL DEFAULT 'pendente',

    data_aprovacao DATETIME,

    FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON DELETE CASCADE
);
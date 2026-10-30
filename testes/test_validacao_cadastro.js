// Testes das regras do static/js/validacao_cadastro.js.
// Rodar na raiz do projeto: node --test testes/test_validacao_cadastro.js

const { test } = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { execFileSync } = require("node:child_process");

// Carrega o script do navegador com um "document" mínimo (sem campos na página)
const raiz = path.join(__dirname, "..");
const contexto = vm.createContext({ document: { getElementById: () => null }, window: {} });
vm.runInContext(
    fs.readFileSync(path.join(raiz, "static", "js", "validacao_cadastro.js"), "utf8")
    + "\n;globalThis.exportados = { validarCPF, calcularIdade, faltandoNaSenha, regrasDadosPessoais, regrasSenha };",
    contexto
);
const { validarCPF, calcularIdade, regrasDadosPessoais: regras, regrasSenha } = contexto.exportados;

test("CPF", () => {
    assert.strictEqual(validarCPF("52998224725"), true);
    assert.strictEqual(validarCPF("11144477735"), true);
    assert.strictEqual(validarCPF("52998224724"), false);
    assert.strictEqual(validarCPF("11111111111"), false);
    assert.strictEqual(regras.cpf(""), "Informe seu CPF.");
    assert.strictEqual(regras.cpf("529.982.247-24"), "CPF inválido.");
    assert.strictEqual(regras.cpf("529.982.247-25"), "");
});

test("CPF: o JS e o servidor concordam", () => {
    // Gera CPFs com todos os dígitos verificadores possíveis e compara com validar_cpf do Python
    const casos = [];
    for (let base = 0; base < 40; base++) {
        const nove = String(123456789 + base * 7919).padStart(9, "0").substring(0, 9);
        for (let dv = 0; dv < 100; dv++) casos.push(nove + String(dv).padStart(2, "0"));
    }
    casos.push("00000000000", "52998224725", "11144477735");

    const python = process.env.PYTHON || (process.platform === "win32"
        ? path.join(raiz, ".venv", "Scripts", "python.exe")
        : path.join(raiz, ".venv", "bin", "python"));
    const saida = execFileSync(python, ["-c",
        "import sys, json; sys.path.insert(0, '.'); from validacoes import validar_cpf; " +
        "print(json.dumps([validar_cpf(c) for c in json.load(sys.stdin)]))"
    ], { cwd: raiz, input: JSON.stringify(casos) });

    const servidor = JSON.parse(saida.toString());
    const validos = servidor.filter(Boolean).length;
    assert.ok(validos > 30, "o teste precisa ter CPFs válidos suficientes");
    casos.forEach((cpf, i) => assert.strictEqual(validarCPF(cpf), servidor[i], cpf));
});

test("data de nascimento", () => {
    assert.strictEqual(calcularIdade(31, 2, 1990), null);
    assert.strictEqual(regras.data_de_nascimento(""), "Informe sua data de nascimento.");
    assert.strictEqual(regras.data_de_nascimento("1990-03-15"), "Use o formato dd/mm/aaaa.");
    assert.strictEqual(regras.data_de_nascimento("31/02/1990"), "Data inválida.");
    assert.strictEqual(regras.data_de_nascimento("15/03/1990"), "");

    const hoje = new Date();
    const dia = String(hoje.getDate()).padStart(2, "0");
    const mes = String(hoje.getMonth() + 1).padStart(2, "0");
    assert.strictEqual(regras.data_de_nascimento(`${dia}/${mes}/${hoje.getFullYear() - 18}`), "");
    assert.strictEqual(regras.data_de_nascimento(`${dia}/${mes}/${hoje.getFullYear() - 17}`), "É preciso ter entre 18 e 100 anos.");
    assert.strictEqual(regras.data_de_nascimento(`${dia}/${mes}/${hoje.getFullYear() - 101}`), "É preciso ter entre 18 e 100 anos.");
});

test("telefone", () => {
    assert.strictEqual(regras.telefone("(11) 98765-4321"), "");
    assert.strictEqual(regras.telefone("(11) 3265-4321"), "");
    assert.strictEqual(regras.telefone(""), "Informe seu telefone.");
    assert.strictEqual(regras.telefone("(11) 8765-432"), "Telefone deve ter DDD e 8 ou 9 dígitos.");
    assert.strictEqual(regras.telefone("(01) 98765-4321"), "DDD inválido.");
    assert.strictEqual(regras.telefone("(11) 88765-4321"), "Celular deve começar com 9.");
});

test("CEP", () => {
    assert.strictEqual(regras.cep("01001-000"), "");
    assert.strictEqual(regras.cep(""), "Informe seu CEP.");
    assert.strictEqual(regras.cep("0100-000"), "CEP deve ter 8 dígitos.");
});

test("senha", () => {
    assert.strictEqual(regrasSenha.senha(""), "Informe uma senha.");
    assert.strictEqual(regrasSenha.senha("Senha@123"), "");
    assert.strictEqual(regrasSenha.senha("senha@123"), "Precisa de uma letra maiúscula.");
    assert.strictEqual(regrasSenha.senha("abc"), "Precisa de 8 caracteres, uma letra maiúscula, um número e um caractere especial.");
    assert.strictEqual(regrasSenha.senha("A1!" + "a".repeat(62)), "A senha deve ter no máximo 64 caracteres.");
    assert.strictEqual(regrasSenha.confirmar_senha(""), "Confirme sua senha.");
});

test("nome", () => {
    assert.strictEqual(regras.nome("Maria"), "");
    assert.strictEqual(regras.sobrenome("da Silva-Souza"), "");
    assert.strictEqual(regras.nome("Maria2"), "Use apenas letras.");
});

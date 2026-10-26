// Edição de um profissional pelo administrador: usa as mesmas regras, máscaras, CRP, foto,
// biografia e busca de CEP do cadastro (validacao_cadastro.js, carregado antes deste).
// O admin pode corrigir todos os dados, inclusive os que o profissional não altera sozinho.

const formEditarProfissional = document.getElementById("formEditarProfissional");
const botaoSalvar = document.getElementById("botaoCadastrar");

limparErrosDoServidor(formEditarProfissional);

const regioesCRP = lerRegioesCRP(document.getElementById("uf_crp"));
const campoFoto = document.getElementById("foto");
const validarFoto = criarValidarFoto(campoFoto);

// As mesmas regras do servidor, em editar_profissional_aprovados no app.py
const validarCampo = criarValidarCampo(
    {
        ...regrasDadosPessoais,
        ...criarRegrasCRP(regioesCRP),
        ...regrasAtuacaoProfissional
    },
    validarFoto
);

aplicarMascaras();
configurarCrp(regioesCRP);
configurarContadorBiografia();
configurarPreviaFoto(campoFoto, validarFoto);
configurarBuscaCep(validarCampo);
configurarValidacao(formEditarProfissional, botaoSalvar, validarCampo);

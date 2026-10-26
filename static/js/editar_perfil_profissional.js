// Edição do perfil pelo próprio profissional: usa as mesmas regras, máscaras, foto, biografia
// e busca de CEP do cadastro (validacao_cadastro.js, carregado antes deste).
// Nome, CPF, e-mail e CRP não são editáveis aqui.

const formEditarPerfil = document.getElementById("formEditarPerfilProfissional");
const botaoSalvar = document.getElementById("botaoCadastrar");

limparErrosDoServidor(formEditarPerfil);

const campoFoto = document.getElementById("foto");
const validarFoto = criarValidarFoto(campoFoto);

// As mesmas regras do servidor, em editar_perfil_profissional no app.py
const validarCampo = criarValidarCampo(
    { ...regrasDadosPessoais, ...regrasAtuacaoProfissional },
    validarFoto
);

aplicarMascaras();
configurarContadorBiografia();
configurarPreviaFoto(campoFoto, validarFoto);
configurarBuscaCep(validarCampo);
configurarValidacao(formEditarPerfil, botaoSalvar, validarCampo);

// Edição de um usuário pelo administrador: usa as mesmas regras, máscaras e busca de CEP
// do cadastro (validacao_cadastro.js, carregado antes deste).
// O admin pode corrigir todos os dados, inclusive o CPF, que o usuário não altera sozinho.

const formEditarUsuario = document.getElementById("formEditarUsuario");
const botaoSalvar = document.getElementById("botaoCadastrar");

limparErrosDoServidor(formEditarUsuario);

// As mesmas regras do servidor, em editar_usuario no app.py
const validarCampo = criarValidarCampo(regrasDadosPessoais);

aplicarMascaras();
configurarBuscaCep(validarCampo);
configurarValidacao(formEditarUsuario, botaoSalvar, validarCampo);

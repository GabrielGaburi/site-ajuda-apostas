// O botão de mostrar/ocultar senha é tratado pelo mostrar_senha.js (carregado no base.html)
// As regras, máscaras e a busca de CEP ficam no validacao_cadastro.js (carregado antes deste)

const formCadastro = document.getElementById("formCadastro");
const botaoCadastrar = document.getElementById("botaoCadastrar");

limparErrosDoServidor(formCadastro);

// As mesmas regras do servidor, em cadastro_usuario no app.py
const validarCampo = criarValidarCampo({ ...regrasDadosPessoais, ...regrasSenha });

aplicarMascaras();
configurarBuscaCep(validarCampo);
configurarValidacao(formCadastro, botaoCadastrar, validarCampo);

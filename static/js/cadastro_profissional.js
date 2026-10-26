// O botão de mostrar/ocultar senha é tratado pelo mostrar_senha.js (carregado no base.html)
// As regras comuns, máscaras, CRP, foto, biografia e a busca de CEP ficam no
// validacao_cadastro.js (carregado antes deste)

const formCadastro = document.getElementById("formCadastroProfissional");
const botaoCadastrar = document.getElementById("botaoCadastrar");

limparErrosDoServidor(formCadastro);

const regioesCRP = lerRegioesCRP(document.getElementById("uf_crp"));
const campoFoto = document.getElementById("foto");
const validarFoto = criarValidarFoto(campoFoto);

// As mesmas regras do servidor, em cadastro_profissional no app.py
const validarCampo = criarValidarCampo(
    {
        ...regrasDadosPessoais,
        ...criarRegrasCRP(regioesCRP),
        ...regrasAtuacaoProfissional,
        ...regrasSenha
    },
    validarFoto
);

aplicarMascaras();
configurarCrp(regioesCRP);
configurarContadorBiografia();
configurarPreviaFoto(campoFoto, validarFoto);
configurarBuscaCep(validarCampo);
configurarValidacao(formCadastro, botaoCadastrar, validarCampo);

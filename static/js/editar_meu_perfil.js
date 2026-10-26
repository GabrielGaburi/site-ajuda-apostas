// Edição dos dados do próprio usuário: usa as mesmas regras, máscaras e busca de CEP do cadastro
// (validacao_cadastro.js, carregado antes deste). O CPF não é editável e fica fora da validação.

const formEditarPerfil = document.getElementById("formEditarPerfil");
const botaoSalvar = document.getElementById("botaoCadastrar");

limparErrosDoServidor(formEditarPerfil);


// =========================
// TROCA DE E-MAIL
// =========================

// A senha atual só é pedida quando o e-mail é alterado (o servidor confere a mesma coisa)
const campoEmail = document.getElementById("email");
const grupoSenhaAtual = document.getElementById("grupoSenhaAtual");
const campoSenhaAtual = document.getElementById("senhaAtual");

function emailFoiAlterado() {
    return campoEmail && campoEmail.value.trim().toLowerCase() !== (campoEmail.dataset.emailAtual || "");
}

if (campoEmail && grupoSenhaAtual && campoSenhaAtual) {
    campoEmail.addEventListener("input", function () {
        const alterado = emailFoiAlterado();
        grupoSenhaAtual.classList.toggle("d-none", !alterado);

        if (!alterado) {
            campoSenhaAtual.value = "";
            limparAviso(campoSenhaAtual);
        }
    });
}

const regrasEdicao = {
    senha_atual: valor => emailFoiAlterado() && !valor ? "Informe sua senha atual para trocar o e-mail." : ""
};

// As mesmas regras do servidor, em editar_meu_perfil no app.py
const validarCampo = criarValidarCampo({ ...regrasDadosPessoais, ...regrasEdicao });

aplicarMascaras();
configurarBuscaCep(validarCampo);
configurarValidacao(formEditarPerfil, botaoSalvar, validarCampo);

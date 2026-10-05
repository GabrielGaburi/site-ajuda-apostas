
console.log("EDITAR_PROFISSIONAL.JS CARREGADO");

document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("formCadastroProfissional");
    const foto = document.getElementById("foto");

    if (!form) {
        return;
    }

    // =====================================================
    // CONTROLA SE O FORMULÁRIO FOI ALTERADO
    // =====================================================

    let formularioAlterado = false;

    form.addEventListener("input", function () {
        formularioAlterado = true;
    });

    form.addEventListener("change", function () {
        formularioAlterado = true;
    });


    // =====================================================
    // PRÉ-VISUALIZAÇÃO DA NOVA FOTO
    // =====================================================

    if (foto) {

        foto.addEventListener("change", function () {

            const arquivo = foto.files[0];

            if (!arquivo) {
                return;
            }

            const extensoesPermitidas = [
                "image/jpeg",
                "image/png"
            ];

            if (!extensoesPermitidas.includes(arquivo.type)) {

                alert("Selecione uma imagem JPG, JPEG ou PNG.");

                foto.value = "";

                return;
            }

            const imagemAtual = document.getElementById("fotoPreview");

            if (!imagemAtual) {
                return;
            }

            const leitor = new FileReader();

            leitor.onload = function (evento) {

                imagemAtual.src = evento.target.result;

            };

            leitor.readAsDataURL(arquivo);

        });

    }


    // =====================================================
    // EVITA SAIR DA PÁGINA SEM SALVAR
    // =====================================================

    window.addEventListener("beforeunload", function (evento) {

        if (!formularioAlterado) {
            return;
        }

        evento.preventDefault();
        evento.returnValue = "";

    });


    // =====================================================
    // ENVIO DO FORMULÁRIO
    // =====================================================

    form.addEventListener("submit", function () {

        formularioAlterado = false;

    });

});
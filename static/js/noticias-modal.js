document.addEventListener("DOMContentLoaded", function () {
    const noticiaModal = document.getElementById('noticiaModal');

    if (!noticiaModal) {
        return;
    }

    noticiaModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;
        if (!button) {
            return;
        }

        const modalTitulo = document.getElementById('modalTitulo');
        const modalIntroducao = document.getElementById('modalIntroducao');
        const linkFonte = document.getElementById('modalFonte');

        if (modalTitulo) {
            modalTitulo.textContent = button.getAttribute('data-titulo');
        }

        if (modalIntroducao) {
            modalIntroducao.textContent = button.getAttribute('data-introducao');
        }

        if (linkFonte) {
            linkFonte.href = button.getAttribute('data-fonte');
        }
    });
});

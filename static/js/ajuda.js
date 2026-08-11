window.irParaLocal = function (lat, lng, nome) {
    const map = window._leafletMap;
    if (!map) {
        return;
    }

    map.setView([lat, lng], 15);
    L.popup()
        .setLatLng([lat, lng])
        .setContent(`<strong>${nome}</strong>`)
        .openOn(map);

    const mapa = document.getElementById("map");
    if (!mapa) {
        return;
    }

    const posicao = mapa.offsetTop;
    window.scrollTo({
        top: posicao - 100,
        behavior: "smooth"
    });
};

function normalizarTexto(texto) {
    return texto
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "");
}

document.addEventListener("DOMContentLoaded", function () {
    const mapElement = document.getElementById("map");
    if (!mapElement) {
        return;
    }

    const locaisJson = mapElement.dataset.locais || "[]";
    let locais = [];
    try {
        locais = JSON.parse(locaisJson);
    } catch (error) {
        locais = [];
    }

    const map = L.map("map").setView([-23.55052, -46.633308], 7);
    window._leafletMap = map;

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);

    const iconeVermelho = new L.Icon({
        iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
        shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });

    const iconeAzul = new L.Icon({
        iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png",
        shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });

    const iconeVerde = new L.Icon({
        iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",
        shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });

    function escolherIcone(tipo) {
        if (tipo.includes("Atendimento")) {
            return iconeVermelho;
        }
        if (tipo.includes("Hospital")) {
            return iconeAzul;
        }
        if (tipo.includes("Grupo")) {
            return iconeVerde;
        }
        return iconeAzul;
    }

    locais.forEach(item => {
        const icone = escolherIcone(item.tipo);
        L.marker([item.lat, item.lng], { icon: icone })
            .addTo(map)
            .bindPopup(`
                <strong>${item.nome}</strong><br>
                ${item.cidade}<br>
                ${item.tipo}<br>
                📍 ${item.endereco}<br>
                📞 ${item.telefone}
            `);
    });

    const buscaCidade = document.getElementById("buscaCidade");
    if (!buscaCidade) {
        return;
    }

    buscaCidade.addEventListener("input", function () {
        const busca = normalizarTexto(this.value);
        const cards = document.querySelectorAll(".card-local");

        cards.forEach(card => {
            const cidade = normalizarTexto(card.dataset.cidade || "");
            card.style.display = cidade.includes(busca) ? "block" : "none";
        });
    });
});

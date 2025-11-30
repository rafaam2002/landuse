var map = L.map("map").setView([37.3891, -5.9845], 8); // Centered on Andalucia approx

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "© OpenStreetMap",
}).addTo(map);

var geoJsonLayer;

document.getElementById("btn-load").addEventListener("click", function () {
  fetch("/api/load_data", { method: "POST" })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        alert(data.message);
      } else {
        alert("Error: " + data.message);
      }
    })
    .catch((error) => alert("Error de red: " + error));
});

document.getElementById("btn-visualize").addEventListener("click", function () {
  var filterVal = document.querySelector('input[name="filter"]:checked').value;

  // Fetch Stats
  fetch(`/api/stats?filter=${filterVal}`)
    .then((response) => response.json())
    .then((data) => {
      document.getElementById("area-display").innerText = data.area_ha + " ha";
    });

  // Fetch Data
  fetch(`/api/data?filter=${filterVal}`)
    .then((response) => response.json())
    .then((data) => {
      if (geoJsonLayer) {
        map.removeLayer(geoJsonLayer);
      }

      geoJsonLayer = L.geoJSON(data, {
        style: function (feature) {
          switch (feature.properties.fclass) {
            case "forest":
              return { color: "forestgreen", fillOpacity: 0.6, weight: 1 };
            case "nature_reserve":
              return { color: "limegreen", fillOpacity: 0.6, weight: 1 };
            default:
              return { color: "blue" };
          }
        },
        onEachFeature: function (feature, layer) {
          if (feature.properties) {
            var name = feature.properties.name || "Sin nombre";
            var area = feature.properties.area_ha || 0;
            var content = `<b>${name}</b><br>Superficie: ${area} ha`;
            layer.bindPopup(content);
            layer.bindTooltip(content);
          }
        },
      }).addTo(map);

      if (data.features.length > 0) {
        map.fitBounds(geoJsonLayer.getBounds());
      } else {
        alert("No se encontraron datos para mostrar.");
      }
    })
    .catch((error) => console.error("Error:", error));
});

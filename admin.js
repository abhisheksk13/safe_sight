const firebaseConfig = {
  apiKey: "AIzaSyDV2X8N1iN0EfbG6XBh4NYE95syHdLi5k4",
  authDomain: "safesightapp.firebaseapp.com",
  projectId: "safesightapp",
  storageBucket: "safesightapp.firebasestorage.app",
  messagingSenderId: "476899350289",
  appId: "1:476899350289:web:4f648986aaa13183895eb0",
  measurementId: "G-8DPZG95K02"
};

firebase.initializeApp(firebaseConfig);
const db = firebase.firestore();
const alertSound = new Audio('sounds/beep.mp3');

let map;
const markers = {};
let adminLocation = null;
let previousAlertIds = new Set(); // ⬅️ Track previously seen alerts

function initMap() {
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: 12.9716, lng: 77.5946 },
    zoom: 12,
  });

  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition((position) => {
      adminLocation = {
        lat: position.coords.latitude,
        lng: position.coords.longitude
      };
      map.setCenter(adminLocation);
    }, () => {
      alert("⚠️ Location access denied. Directions may not work properly.");
    });
  }

  loadAlerts();
}
window.initMap = initMap;

function loadAlerts() {
  db.collection("emergencies").onSnapshot((snapshot) => {
    document.querySelector("#alertsTable tbody").innerHTML = "";

    let currentAlertIds = new Set();
    let isNewAlert = false;

    snapshot.forEach(doc => {
      const data = doc.data();
      const id = doc.id;
      const pos = { lat: data.latitude, lng: data.longitude };

      currentAlertIds.add(id);
      if (!previousAlertIds.has(id)) {
        isNewAlert = true; // New alert detected
      }

      // Marker
      if (!markers[id]) {
        const marker = new google.maps.Marker({
          position: pos,
          map: map,
          title: data.description,
        });
        markers[id] = marker;
      }

      // Table row'
      const timestamp = data.timestamp?.toDate?.() || new Date();
      const timeString = timestamp.toLocaleString();

      const tr = document.createElement("tr");

      tr.innerHTML = `
      <td>${data.description}</td>
      <td>${timeString}</td>
      <td>
        <select onchange="updateStatus('${id}', this.value)">
          <option value="New Alert" ${data.status === "New Alert" ? "selected" : ""}>New Alert</option>
          <option value="Checked" ${data.status === "Checked" ? "selected" : ""}>Checked</option>
          <option value="In Process" ${data.status === "In Process" ? "selected" : ""}>In Process</option>
          <option value="Action Taken" ${data.status === "Action Taken" ? "selected" : ""}>Action Taken</option>
        </select>
      </td>
      <td>
        ${data.videoUrl ? `<a href="${data.videoUrl}" target="_blank">View Video</a>` : "No Video"}
      </td>
      <td>
        <button onclick="goToDirection(${data.latitude}, ${data.longitude})">➡️ Navigate</button>
      </td>
      <td>
        <button onclick="deleteAlert('${id}')">🗑️ Delete</button>
      </td>
      `;
      document.querySelector("#alertsTable tbody").appendChild(tr);
    });

    // Remove markers that no longer exist
    const currentIds = snapshot.docs.map(doc => doc.id);
    for (const id in markers) {
      if (!currentIds.includes(id)) {
        markers[id].setMap(null);
        delete markers[id];
      }
    }

    // 🔊 Play sound if a new alert is detected
    if (isNewAlert) {
      alertSound.play();
    }

    // Update known alerts
    previousAlertIds = currentAlertIds;
  });
}

async function updateStatus(id, newStatus) {
  try {
    await db.collection("emergencies").doc(id).update({ status: newStatus });
    alert("✅ Status updated!");
  } catch (error) {
    alert("❌ Error updating status: " + error.message);
  }
}

async function deleteAlert(id) {
  if (!confirm("Are you sure you want to delete this alert?")) return;

  try {
    await db.collection("emergencies").doc(id).delete();
    if (markers[id]) {
      markers[id].setMap(null);
      delete markers[id];
    }
    alert("🗑️ Alert deleted!");
  } catch (error) {
    alert("❌ Error deleting alert: " + error.message);
  }
}

function goToDirection(destLat, destLng) {
  if (!adminLocation) {
    alert("⚠️ Admin location not found. Allow location permission.");
    return;
  }

  const origin = `${adminLocation.lat},${adminLocation.lng}`;
  const destination = `${destLat},${destLng}`;
  const url = `https://www.google.com/maps/dir/?api=1&origin=${origin}&destination=${destination}&travelmode=driving`;
  window.open(url, "_blank");
}

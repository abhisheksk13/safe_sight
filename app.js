// Firebase Config
const firebaseConfig = {
  USE_FIREBASE_CREDENTRIALS
  };
  
  firebase.initializeApp(firebaseConfig);
  const db = firebase.firestore();
  const storage = firebase.storage();
  const auth = firebase.auth();
  
  let map, userMarker, verifiedUser = false;
  
  // Initialize Google Map
  function initMap() {
    map = new google.maps.Map(document.getElementById("map"), {
      center: { lat: 12.9716, lng: 77.5946 },
      zoom: 12,
    });
  
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((position) => {
        const pos = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        };
        map.setCenter(pos);
        userMarker = new google.maps.Marker({
          position: pos,
          map: map,
          title: "You are here",
        });
        loadNearbyEmergencies(pos);
      }, () => alert("Error: Location access denied."));
    }
  }
  window.initMap = initMap;
  
  // Distance Helper
  function getDistance(pos1, pos2) {
    const R = 6371;
    const dLat = (pos2.lat - pos1.lat) * Math.PI / 180;
    const dLon = (pos2.lng - pos1.lng) * Math.PI / 180;
    const a = Math.sin(dLat/2)**2 +
              Math.cos(pos1.lat * Math.PI / 180) * Math.cos(pos2.lat * Math.PI / 180) *
              Math.sin(dLon/2)**2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }
  
  // Load Nearby Emergencies
  async function loadNearbyEmergencies(userPos) {
    try {
      const snapshot = await db.collection("emergencies").get();
      snapshot.forEach(doc => {
        const data = doc.data();
        const pos = { lat: data.latitude, lng: data.longitude };
        if (getDistance(userPos, pos) < 5) {
          new google.maps.Marker({
            position: pos,
            map: map,
            icon: "http://maps.google.com/mapfiles/ms/icons/red-dot.png",
            title: data.description
          });
        }
      });
    } catch (error) {
      console.error("Error loading emergencies:", error);
    }
  }
  
  // OTP - Send
  window.sendOTP = () => {
    const phoneNumber = document.getElementById("phone").value;
    if (!phoneNumber.startsWith("+")) {
      alert("Please use international format, e.g., +91...");
      return;
    }
  
    window.recaptchaVerifier = new firebase.auth.RecaptchaVerifier('recaptcha-container');
    auth.signInWithPhoneNumber(phoneNumber, window.recaptchaVerifier)
      .then((result) => {
        window.confirmationResult = result;
        alert("OTP sent!");
      }).catch(error => alert("Error sending OTP: " + error.message));
  };
  
  // OTP - Verify
  window.verifyOTP = () => {
    const otp = document.getElementById("otp").value;
    confirmationResult.confirm(otp).then(() => {
      alert("Phone verified ✅");
      document.getElementById("alertButton").disabled = false;
      verifiedUser = true;
    }).catch(() => alert("Invalid OTP"));
  };
  
  // Emergency Alert Button
  document.getElementById("alertButton").addEventListener("click", async () => {
    if (!verifiedUser) return alert("Please verify your phone first.");
    if (!userMarker) return alert("User location not found.");
  
    const username = document.getElementById("username").value.trim();
    const description = document.getElementById("description").value.trim();
    const videoFile = document.getElementById("video").files[0];
    const progressBar = document.getElementById("progressBar");
  
    if (!username) return alert("Please enter your name!");
    if (!description) return alert("Please enter a problem description!");
  
    const emergencyData = {
      username: username,
      latitude: userMarker.getPosition().lat(),
      longitude: userMarker.getPosition().lng(),
      timestamp: new Date(),
      status: "New Alert",
      description: description,
      videoUrl: null
    };
  
    try {
      if (videoFile) {
        const storageRef = storage.ref('videos/' + Date.now() + '_' + videoFile.name);
        const uploadTask = storageRef.put(videoFile);
        uploadTask.on('state_changed',
          snapshot => {
            const progress = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
            progressBar.style.width = progress + "%";
          },
          error => { throw error; },
          async () => {
            const downloadURL = await uploadTask.snapshot.ref.getDownloadURL();
            emergencyData.videoUrl = downloadURL;
            await db.collection("emergencies").add(emergencyData);
            resetForm();
          }
        );
      } else {
        await db.collection("emergencies").add(emergencyData);
        resetForm();
      }
    } catch (error) {
      alert("Error: " + error.message);
      progressBar.style.width = "0%";
    }
  });
  
  // Reset Button
  document.getElementById("resetButton").addEventListener("click", () => {
    if (confirm("Are you sure you want to reset the form?")) {
      resetForm();
    }
  });
  
  // Reset Form Function
  function resetForm() {
    document.getElementById("username").value = "";
    document.getElementById("phone").value = "";
    document.getElementById("otp").value = "";
    document.getElementById("description").value = "";
    document.getElementById("video").value = "";
    document.getElementById("progressBar").style.width = "0%";
  }
  

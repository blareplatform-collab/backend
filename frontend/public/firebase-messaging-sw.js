importScripts("https://www.gstatic.com/firebasejs/10.0.0/firebase-app-compat.js")
importScripts("https://www.gstatic.com/firebasejs/10.0.0/firebase-messaging-compat.js")

firebase.initializeApp({
  apiKey: "AIzaSyB9zOknS9836wHYqQTpabEebG11aSVicPA",
  authDomain: "blare-dad91.firebaseapp.com",
  projectId: "blare-dad91",
  storageBucket: "blare-dad91.firebasestorage.app",
  messagingSenderId: "140352497500",
  appId: "1:140352497500:web:b88693ce77c50d87b78399",
})

const messaging = firebase.messaging()

messaging.onBackgroundMessage((payload) => {
  const { title, body } = payload.notification
  self.registration.showNotification(title, {
    body,
    icon: "/icon.png",
    badge: "/icon.png",
    vibrate: [200, 100, 200],
  })
})

/* eslint-disable no-undef */
// Background push handler. Config can't reach a static file via Next.js env vars,
// so it's passed as query params on the registration URL (see registerPush.ts).
importScripts("https://www.gstatic.com/firebasejs/11.0.0/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/11.0.0/firebase-messaging-compat.js");

const params = new URL(self.location.href).searchParams;

firebase.initializeApp({
  apiKey: params.get("apiKey"),
  authDomain: params.get("authDomain"),
  projectId: params.get("projectId"),
  storageBucket: params.get("storageBucket"),
  messagingSenderId: params.get("messagingSenderId"),
  appId: params.get("appId"),
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  const title = payload.notification?.title || "SportsOS";
  const body = payload.notification?.body || "";
  self.registration.showNotification(title, { body, data: payload.data || {} });
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const bookingId = event.notification.data?.booking_id;
  const url = bookingId ? `/bookings/${bookingId}` : "/notifications";
  event.waitUntil(self.clients.openWindow(url));
});

"use client";

import { getToken } from "firebase/messaging";
import { firebaseConfig, firebaseConfigured, getMessagingIfSupported } from "@/lib/firebase";
import { apiFetch } from "@/lib/api/client";

export const pushSupported =
  typeof window !== "undefined" &&
  window.isSecureContext &&
  "serviceWorker" in navigator &&
  "Notification" in window &&
  firebaseConfigured;

/** Requests notification permission, registers the background service worker,
 * and hands the resulting FCM token to the backend. Only works over HTTPS
 * (or localhost) — the server needs TLS before this activates in production. */
export async function enablePushNotifications(): Promise<boolean> {
  if (!pushSupported) return false;

  const messaging = await getMessagingIfSupported();
  if (!messaging) return false;

  const permission = await Notification.requestPermission();
  if (permission !== "granted") return false;

  const swParams = new URLSearchParams(
    Object.entries(firebaseConfig).filter((entry): entry is [string, string] => Boolean(entry[1]))
  );
  const registration = await navigator.serviceWorker.register(
    `/firebase-messaging-sw.js?${swParams.toString()}`
  );

  const vapidKey = process.env.NEXT_PUBLIC_FIREBASE_VAPID_KEY;
  const token = await getToken(messaging, { vapidKey, serviceWorkerRegistration: registration });
  if (!token) return false;

  await apiFetch("/notifications/me/device-tokens", {
    method: "POST",
    body: JSON.stringify({ platform: "web", token }),
  });
  return true;
}

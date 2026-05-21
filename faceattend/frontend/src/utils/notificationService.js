
// frontend/src/utils/notificationService.js

/**
 * Requests notification permission from the browser.
 * returns Promise<boolean> - true if granted
 */
export async function requestNotificationPermission() {
  if (!("Notification" in window)) {
    console.warn("This browser does not support desktop notifications");
    return false;
  }

  let permission = Notification.permission;

  if (permission === "default") {
    permission = await Notification.requestPermission();
  }

  return permission === "granted";
}

/**
 * Ensures the service worker is ready and returns the registration.
 */
export async function getServiceWorkerRegistration() {
  if ("serviceWorker" in navigator) {
    try {
      const registration = await navigator.serviceWorker.ready;
      return registration;
    } catch (error) {
      console.error("Service Worker not ready:", error);
      return null;
    }
  }
  return null;
}

/**
 * Shows a system notification via the Service Worker.
 * This ensures notifications appear even if the app is in the background.
 */
export async function showSystemNotification(title, options = {}) {
  const granted = await requestNotificationPermission();
  
  if (!granted) {
    console.warn("Notification permission denied");
    return;
  }

  const registration = await getServiceWorkerRegistration();

  if (registration) {
    // Use Service Worker to show notification (System Level)
    try {
      await registration.showNotification(title, {
        icon: '/pwa-192x192.png',
        badge: '/pwa-192x192.png',
        vibrate: [200, 100, 200],
        ...options
      });
    } catch (e) {
      console.error("Failed to show SW notification:", e);
      // Fallback to standard API if SW fails
      new Notification(title, options);
    }
  } else {
    // Fallback if no SW support
    console.warn("No Service Worker found, falling back to standard Notification");
    new Notification(title, options);
  }
}

/**
 * Check current permission state
 */
export function getNotificationPermissionState() {
    if (!("Notification" in window)) return "denied";
    return Notification.permission;
}

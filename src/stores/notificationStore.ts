import { create } from "zustand";
import { NotificationMessage } from "../types/common.types";

interface NotificationState {
  notifications: NotificationMessage[];
  maxNotifications: number;

  // Actions
  addNotification: (
    notification: Omit<NotificationMessage, "id" | "timestamp">
  ) => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
  markAsRead: (id: string) => void;

  // Convenience methods
  showSuccess: (title: string, message: string, duration?: number) => void;
  showError: (title: string, message: string, duration?: number) => void;
  showWarning: (title: string, message: string, duration?: number) => void;
  showInfo: (title: string, message: string, duration?: number) => void;
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  maxNotifications: 5,

  addNotification: (notification) => {
    const id = `notification_${Date.now()}_${Math.random()
      .toString(36)
      .substr(2, 9)}`;
    const newNotification: NotificationMessage = {
      ...notification,
      id,
      timestamp: new Date().toISOString(),
    };

    set((state) => {
      const newNotifications = [newNotification, ...state.notifications];

      // Keep only the latest maxNotifications
      if (newNotifications.length > state.maxNotifications) {
        newNotifications.splice(state.maxNotifications);
      }

      return { notifications: newNotifications };
    });

    // Auto-remove after duration
    if (notification.duration && notification.duration > 0) {
      setTimeout(() => {
        get().removeNotification(id);
      }, notification.duration);
    }
  },

  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),

  clearAll: () => set({ notifications: [] }),

  markAsRead: (id) =>
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n
      ),
    })),

  // Convenience methods
  showSuccess: (title, message, duration = 4000) => {
    get().addNotification({ type: "success", title, message, duration });
  },

  showError: (title, message, duration = 6000) => {
    get().addNotification({ type: "error", title, message, duration });
  },

  showWarning: (title, message, duration = 5000) => {
    get().addNotification({ type: "warning", title, message, duration });
  },

  showInfo: (title, message, duration = 4000) => {
    get().addNotification({ type: "info", title, message, duration });
  },
}));

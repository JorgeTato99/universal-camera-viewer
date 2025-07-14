/**
 * Common Types & Interfaces
 * Shared types across the application
 */

export interface AppConfig {
  app_name: string;
  version: string;
  theme_mode: "light" | "dark" | "system";
  language: string;
  auto_save: boolean;
  notifications_enabled: boolean;
}

export interface MenuItem {
  id: string;
  label: string;
  icon?: string;
  path?: string;
  children?: MenuItem[];
  disabled?: boolean;
  badge?: string | number;
}

export interface NavigationState {
  currentPath: string;
  previousPath?: string;
  breadcrumbs: string[];
}

export interface NotificationMessage {
  id: string;
  type: "success" | "error" | "warning" | "info";
  title: string;
  message: string;
  duration?: number;
  timestamp: string;
  actions?: NotificationAction[];
}

export interface NotificationAction {
  label: string;
  action: () => void;
  primary?: boolean;
}

export interface LoadingState {
  isLoading: boolean;
  message?: string;
  progress?: number;
}

export interface ErrorState {
  hasError: boolean;
  error?: Error | string;
  errorCode?: string;
  timestamp?: string;
}

export interface PaginationParams {
  page: number;
  limit: number;
  total?: number;
}

export interface SortParams {
  field: string;
  direction: "asc" | "desc";
}

export interface FilterParams {
  [key: string]: any;
}

export interface SearchParams {
  query: string;
  filters?: FilterParams;
  sort?: SortParams;
  pagination?: PaginationParams;
}

export interface ModalState {
  isOpen: boolean;
  modalType?: string;
  data?: any;
}

export interface Theme {
  mode: "light" | "dark";
  primaryColor: string;
  secondaryColor: string;
  backgroundColor: string;
  surfaceColor: string;
  textColor: string;
}

export interface UserPreferences {
  theme: Theme;
  language: string;
  notifications: boolean;
  autoSave: boolean;
  defaultView: string;
  gridColumns: number;
}

export type Status = "idle" | "loading" | "success" | "error";

export type AsyncState<T> = {
  data?: T;
  status: Status;
  error?: string;
  lastUpdated?: string;
};

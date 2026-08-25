/// <reference types="vite/client" />

interface ImportMetaEnv {
  /**
   * Optional override for the backend base URL (e.g. http://localhost:8000).
   * When unset, the app uses same-origin requests, which the Vite dev server
   * proxies to the backend (see vite.config.ts). Set this for a deployed build
   * or a backend that is not behind the Vite proxy.
   */
  readonly VITE_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

import { createBrowserRouter, Navigate } from "react-router";
import AppLayout from "./layout/AppLayout";
import Overview from "./pages/Overview";
import LiveMonitor from "./pages/LiveMonitor";
import Stations from "./pages/Stations";
import StationDetail from "./pages/StationDetail";
import Anomalies from "./pages/Anomalies";
import Maintenance from "./pages/Maintenance";
import Analytics from "./pages/Analytics";
import MapView from "./pages/MapView";
import Settings from "./pages/Settings";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: AppLayout,
    children: [
      { index: true, Component: () => <Navigate to="/overview" replace /> },
      { path: "overview", Component: Overview, handle: { title: "Overview" } },
      { path: "live", Component: LiveMonitor, handle: { title: "Live Monitor" } },
      { path: "stations", Component: Stations, handle: { title: "Stations" } },
      { path: "stations/:id", Component: StationDetail, handle: { title: "Station detail" } },
      { path: "anomalies", Component: Anomalies, handle: { title: "Anomalies" } },
      { path: "maintenance", Component: Maintenance, handle: { title: "Maintenance & sensor health" } },
      { path: "analytics", Component: Analytics, handle: { title: "Model analytics" } },
      { path: "map", Component: MapView, handle: { title: "Network map" } },
      { path: "settings", Component: Settings, handle: { title: "Settings" } },
      { path: "*", Component: () => <Navigate to="/overview" replace /> },
    ],
  },
]);

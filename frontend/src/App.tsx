import { RouterProvider } from "react-router";
import { router } from "./routes";
import { StreamProvider } from "./lib/StreamProvider";

export default function App() {
  return (
    <StreamProvider>
      <RouterProvider router={router} />
    </StreamProvider>
  );
}

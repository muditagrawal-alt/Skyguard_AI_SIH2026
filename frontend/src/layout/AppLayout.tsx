import { Outlet, useMatches, useLocation } from "react-router";
import NavRail from "./NavRail";
import TopBar from "./TopBar";

type Handle = { title?: string };

export default function AppLayout() {
  const matches = useMatches();
  const { pathname } = useLocation();
  const title =
    [...matches].reverse().find((m) => (m.handle as Handle)?.title)?.handle as Handle | undefined;

  return (
    <div className="flex h-full w-full overflow-hidden bg-stratus text-ink">
      <div className="hidden lg:block">
        <NavRail />
      </div>
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar title={title?.title ?? "SkyGuard AI"} />
        <main className="flex-1 overflow-y-auto">
          {/* key on the route so each view plays one quiet rise-in on mount */}
          <div key={pathname} className="rise-in mx-auto max-w-[1520px] px-7 py-7">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}

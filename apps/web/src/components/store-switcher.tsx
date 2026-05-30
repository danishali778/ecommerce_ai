import { useLocation, useNavigate } from "react-router-dom";

import { Select } from "@frontend/ui";

import { useAppState } from "@/hooks/use-app-state";
import { useAuth } from "@/hooks/use-auth";

export function StoreSwitcher() {
  const { me } = useAuth();
  const { selectedStoreId, setSelectedStoreId } = useAppState();
  const navigate = useNavigate();
  const location = useLocation();
  const stores = me?.accessible_stores ?? [];

  if (!stores.length) return null;

  const onChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const next = event.target.value;
    setSelectedStoreId(next);

    if (location.pathname.startsWith("/app/stores/")) {
      navigate(`/app/stores/${next}`);
      return;
    }
    if (location.pathname.startsWith("/app/catalog/")) {
      navigate(`/app/catalog/${next}/products`);
      return;
    }
    if (location.pathname.startsWith("/app/support/")) {
      navigate(`/app/support/${next}/conversations`);
      return;
    }
    if (location.pathname.startsWith("/app/fraud/")) {
      navigate(`/app/fraud/${next}/reviews`);
      return;
    }
    if (location.pathname.startsWith("/app/inventory/")) {
      navigate(`/app/inventory/${next}`);
      return;
    }
    if (location.pathname.startsWith("/app/analytics/")) {
      navigate(`/app/analytics/${next}`);
      return;
    }
    if (location.pathname.startsWith("/app/runtime/")) {
      navigate(`/app/runtime/workflows/${next}`);
    }
  };

  return (
    <div className="min-w-0 flex-1 sm:min-w-[14rem] xl:w-[17rem] xl:flex-none">
      <div className="mb-1.5 px-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">Active store</div>
      <Select
        value={selectedStoreId ?? stores[0].id}
        onChange={onChange}
        className="h-11 rounded-xl border-slate-200 bg-white px-3.5 shadow-none focus:border-accent-300 focus:ring-4 focus:ring-accent-100"
      >
        {stores.map((store) => (
          <option key={store.id} value={store.id}>
            {store.name}
          </option>
        ))}
      </Select>
    </div>
  );
}

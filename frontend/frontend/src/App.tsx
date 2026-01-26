import { useEffect, useState } from "react";
import { supabase } from "./lib/supabase";
import { Ticket } from "./types/ticket";

export default function App() {
  const [tickets, setTickets] = useState<Ticket[]>([]);

  // Load initial tickets
  useEffect(() => {
    supabase
      .from("tickets")
      .select("*")
      .order("created_at", { ascending: false })
      .then(({ data }) => {
        if (data) setTickets(data);
      });

    // Realtime subscription
    const channel = supabase
      .channel("tickets-realtime")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "tickets" },
        (payload) => {
          setTickets((prev) => {
            const updated = payload.new as Ticket;
            const others = prev.filter((t) => t.id !== updated.id);
            return [updated, ...others];
          });
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <h1 className="text-2xl font-bold mb-6">
        AI Support Co-Pilot
      </h1>

      <div className="grid gap-4">
        {tickets.map((t) => (
          <div
            key={t.id}
            className="bg-white p-4 rounded-lg shadow border"
          >
            <p className="text-sm text-gray-500">
              {new Date(t.created_at).toLocaleString()}
            </p>

            <p className="mt-2">{t.description}</p>

            <div className="mt-3 flex gap-3 text-sm">
              <span className="px-2 py-1 rounded bg-blue-100">
                {t.category ?? "Pendiente"}
              </span>

              <span
                className={`px-2 py-1 rounded ${
                  t.sentiment === "Negativo"
                    ? "bg-red-200"
                    : t.sentiment === "Positivo"
                    ? "bg-green-200"
                    : "bg-gray-200"
                }`}
              >
                {t.sentiment ?? "—"}
              </span>

              {!t.processed && (
                <span className="px-2 py-1 rounded bg-yellow-200">
                  Procesando
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}


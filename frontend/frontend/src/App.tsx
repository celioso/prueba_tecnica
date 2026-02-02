import { useState } from "react";
import { supabase } from "./lib/supabase";

export default function TicketSimulator() {
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;

    setLoading(true);
    try {
      // 1. Insertar ticket en Supabase
      const { data, error } = await supabase
        .from("tickets")
        .insert([{ description, processed: false }])
        .select()
        .single();

      if (error) throw error;

      // Reemplaza con tu URL real de Render
      const API_URL = "https://prueba-tecnica-krdj.onrender.com/process-ticket";
      
      await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticket_id: data.id,
          description: data.description
        }),
      });

      setDescription("");
      alert("Ticket enviado y procesándose por la IA");
    } catch (err) {
      console.error(err);
      alert("Error al simular el ticket");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto mb-10 bg-white p-6 rounded-xl shadow-sm border border-blue-100">
      <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
        <span className="flex h-3 w-3 rounded-full bg-blue-500"></span>
        Simular Nuevo Ticket
      </h2>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Ej: No puedo acceder a mi factura del mes pasado..."
          className="flex-1 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 text-sm"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading}
          className={`px-6 py-3 rounded-lg font-bold text-white transition-all ${
            loading ? "bg-gray-400" : "bg-blue-600 hover:bg-blue-700"
          }`}
        >
          {loading ? "Enviando..." : "Enviar a IA"}
        </button>
      </form>
    </div>
  );
}
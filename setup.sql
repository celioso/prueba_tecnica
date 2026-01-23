-- Crear la tabla de tickets
CREATE TYPE ticket_category AS ENUM ('Técnico', 'Facturación', 'Comercial');
CREATE TYPE ticket_sentiment AS ENUM ('Positivo', 'Neutral', 'Negativo');

CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    description TEXT NOT NULL,
    category ticket_category,
    sentiment ticket_sentiment,
    processed BOOLEAN DEFAULT false
);

ALTER PUBLICATION supabase_realtime ADD TABLE tickets;

ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Permitir todo a todos" ON tickets FOR ALL USING (true) WITH CHECK (true);
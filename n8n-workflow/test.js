fetch("https://TU_N8N_URL/webhook/new-ticket", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
        ticket_id: "UUID",
        description: "Texto del ticket"
    })
});

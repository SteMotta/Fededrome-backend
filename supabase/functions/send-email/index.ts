// index.ts - Custom Auth Hook per l'invio di email via Resend

interface WebhookPayload {
  user: {
    email: string;
    id: string;
  };
  email_data: {
    email_action_type: string;
    token_hash: string;
    redirect_to: string;
  };
}

Deno.serve(async (req) => {
  // 1. Forza solo il metodo POST per sicurezza
  if (req.method !== "POST") {
    return new Response(
      JSON.stringify({ error: "Method not allowed. Only POST is accepted." }), 
      { status: 405, headers: { "Content-Type": "application/json" } }
    )
  }

  // 2. Recupera e valida la chiave API di Resend dinamica
  const resendApiKey = Deno.env.get("RESEND_API_KEY")
  if (!resendApiKey) {
    console.error("CRITICAL ERROR: RESEND_API_KEY non è configurata nelle variabili del container.")
    return new Response(
      JSON.stringify({ error: "Server misconfiguration: missing email API key." }), 
      { status: 500, headers: { "Content-Type": "application/json" } }
    )
  }

  const supabasePublicUrl = Deno.env.get("SUPABASE_PUBLIC_URL") || "https://db.fededrome.app"

  try {
    // 3. Parsing sicuro del payload JSON
    let payload: WebhookPayload
    try {
      payload = await req.json()
    } catch {
      return new Response(
        JSON.stringify({ error: "Malformed JSON payload." }), 
        { status: 400, headers: { "Content-Type": "application/json" } }
      )
    }

    // 4. Validazione dei campi essenziali
    if (!payload?.user?.email || !payload?.email_data?.email_action_type || !payload?.email_data?.token_hash) {
      return new Response(
        JSON.stringify({ error: "Missing required fields in webhook payload." }), 
        { status: 400, headers: { "Content-Type": "application/json" } }
      )
    }

    const { email_action_type, token_hash, redirect_to } = payload.email_data
    const toEmail = payload.user.email

    // Costruisci il link di conferma per l'utente (redirect_to va URL-encoded per preservare lo schema custom fededrome://)
    const confirmLink = `${supabasePublicUrl}/auth/v1/verify?token=${token_hash}&type=${email_action_type}&redirect_to=${encodeURIComponent(redirect_to)}`

    let subject = ""
    let htmlContent = ""

    // 5. Composizione dei template email (signup e recovery)
    if (email_action_type === "signup") {
      subject = "Benvenuto su Fededrome! Conferma il tuo account"
      htmlContent = `
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #121212; color: #ffffff; padding: 20px; text-align: center;">
            <div style="max-width: 600px; margin: auto; background-color: #1a1a1a; padding: 30px; border-radius: 8px; border: 1px solid #333;">
                <h1 style="color: #E21227;">Benvenuto su Fededrome!</h1>
                <p>Grazie per esserti registrato. Per confermare il tuo account e attivare il tuo profilo, clicca sul link sottostante:</p>
                <p style="margin: 30px 0;">
                    <a href="${confirmLink}" style="padding: 12px 24px; background-color: #E21227; color: #ffffff; text-decoration: none; border-radius: 5px; font-weight: bold;">Conferma Account</a>
                </p>
                <p style="font-size: 12px; color: #888;">Se il pulsante non funziona, copia e incolla questo URL nel tuo browser:</p>
                <p style="font-size: 12px; color: #E21227; word-wrap: break-word;">${confirmLink}</p>
            </div>
        </body>
        </html>
      `
    } else if (email_action_type === "recovery") {
      subject = "Recupero Password - Fededrome"
      htmlContent = `
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #121212; color: #ffffff; padding: 20px; text-align: center;">
            <div style="max-width: 600px; margin: auto; background-color: #1a1a1a; padding: 30px; border-radius: 8px; border: 1px solid #333;">
                <h1 style="color: #E21227;">Reimposta la tua Password</h1>
                <p>Hai richiesto il reset della password per il tuo account Fededrome. Clicca sul link sottostante per impostare una nuova password:</p>
                <p style="margin: 30px 0;">
                    <a href="${confirmLink}" style="padding: 12px 24px; background-color: #E21227; color: #ffffff; text-decoration: none; border-radius: 5px; font-weight: bold;">Reimposta Password</a>
                </p>
                <p style="font-size: 12px; color: #888;">Se il pulsante non funziona, copia e incolla questo URL nel tuo browser:</p>
                <p style="font-size: 12px; color: #E21227; word-wrap: break-word;">${confirmLink}</p>
            </div>
        </body>
        </html>
      `
    } else {
      // Fallback generico per altri eventi
      subject = `Verifica Account Fededrome - ${email_action_type}`
      htmlContent = `
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #121212; color: #ffffff; padding: 20px; text-align: center;">
            <div style="max-width: 600px; margin: auto; background-color: #1a1a1a; padding: 30px; border-radius: 8px; border: 1px solid #333;">
                <h1 style="color: #E21227;">Verifica il tuo Account</h1>
                <p>È stata richiesta un'azione che richiede la verifica dell'indirizzo email per il tipo: <strong>${email_action_type}</strong>.</p>
                <p style="margin: 30px 0;">
                    <a href="${confirmLink}" style="padding: 12px 24px; background-color: #E21227; color: #ffffff; text-decoration: none; border-radius: 5px; font-weight: bold;">Procedi alla verifica</a>
                </p>
                <p style="font-size: 12px; color: #888;">Se il pulsante non funziona, copia e incolla questo URL nel tuo browser:</p>
                <p style="font-size: 12px; color: #E21227; word-wrap: break-word;">${confirmLink}</p>
            </div>
        </body>
        </html>
      `
    }

    // 6. Chiamata HTTP asincrona all'API di Resend
    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${resendApiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: "Fededrome <noreply@fededrome.app>",
        to: [toEmail],
        subject: subject,
        html: htmlContent,
      }),
    })

    if (!res.ok) {
      const errText = await res.text()
      console.error(`Errore risposta Resend API: ${res.status} - ${errText}`)
      return new Response(
        JSON.stringify({ error: "Failed to dispatch email via provider." }), 
        { status: 502, headers: { "Content-Type": "application/json" } }
      )
    }

    // Risposta di successo per Supabase Auth
    return new Response(
      JSON.stringify({ status: "success" }), 
      { status: 200, headers: { "Content-Type": "application/json" } }
    )

  } catch (error) {
    console.error(`Errore generico Edge Function send-email: ${error.message}`)
    return new Response(
      JSON.stringify({ error: "Internal server error in custom email hook." }), 
      { status: 500, headers: { "Content-Type": "application/json" } }
    )
  }
})

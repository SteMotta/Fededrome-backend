import { serve } from "https://deno.land/std@0.177.0/http/server.ts"

const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY")
const SUPABASE_PUBLIC_URL = Deno.env.get("SUPABASE_PUBLIC_URL") || "https://db.fededrome.app"

interface WebhookPayload {
  user: {
    email: string;
    id: string;
  };
  email: {
    email_action_type: string;
    token_hash: string;
    redirect_url: string;
  };
}

serve(async (req) => {
  try {
    const payload: WebhookPayload = await req.json()
    const { email_action_type, token_hash, redirect_url } = payload.email
    const toEmail = payload.user.email

    // Costruisci il link di conferma per il client
    const confirmLink = `${SUPABASE_PUBLIC_URL}/auth/v1/verify?token=${token_hash}&type=${email_action_type}&redirect_to=${redirect_url}`

    let subject = ""
    let htmlContent = ""

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
      // Fallback per altri tipi di email
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

    if (!RESEND_API_KEY) {
      console.error("Errore: RESEND_API_KEY non configurata nelle Edge Functions.")
      return new Response(JSON.stringify({ error: "Missing Resend API Key" }), { status: 500 })
    }

    // Effettua la richiesta HTTP POST all'API di Resend
    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${RESEND_API_KEY}`,
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
      return new Response(JSON.stringify({ error: "Failed to send email via Resend" }), { status: 500 })
    }

    return new Response(JSON.stringify({ status: "success" }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    })

  } catch (error) {
    console.error(`Errore Edge Function: ${error.message}`)
    return new Response(JSON.stringify({ error: error.message }), { status: 500 })
  }
})

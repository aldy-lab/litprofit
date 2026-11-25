// ============================================================
// USERS — who may sign in to the calculator, and as what
// ============================================================
// Creating an account, blocking one, or handing out a sign-in link needs the
// service role, and the service role must never be in the page: the
// calculator is a static file, and a key in it is a published key. So this
// function holds it (Supabase injects SUPABASE_SERVICE_ROLE_KEY into every
// function; it is not in this repository and not in any file) and does five
// things for one kind of caller only: an admin.
//
// THE CHECK, AND WHERE IT LIVES
// -----------------------------
// The caller's own token is verified with the auth server, and their role is
// read from profiles with the elevated client -- not taken from anything the
// browser sent. A tab hidden in JavaScript is not a permission; this is.
//
// NO PASSWORDS PASS THROUGH HERE
// ------------------------------
// A new person gets a one-time link, not a password. The admin sends the
// link (any channel); the person opens it and chooses their own password on
// the calculator's own page. Nobody else ever knows it, nothing stores it in
// plain text, and the admin cannot read it back. The same link, generated
// again, is how a forgotten password is replaced -- the project's mail is
// Supabase's built-in sender, which only delivers to the project team, so a
// "forgot password" e-mail to an employee does not arrive.
//
// NOTHING IS DELETED
// ------------------
// A person who leaves is BLOCKED. Deleting the account would cascade into
// profiles and take the name off every row they ever closed or signed; a
// block keeps the history and can be undone.
// ============================================================

import { createClient } from "npm:@supabase/supabase-js@2";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, content-type, apikey",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS, "Content-Type": "application/json" },
  });

const ROLES = ["admin", "manager", "staff"];
const FOREVER = "876000h"; // a hundred years: Supabase has no "until unblocked"

/* Where a link may send someone. Anything else falls back to the project's
   own Site URL -- an open redirect in a sign-in link is a phishing kit. */
function safeRedirect(u: unknown): string | undefined {
  if (typeof u !== "string") return undefined;
  try {
    const url = new URL(u);
    const ok = url.hostname === "litprofit.com" || url.hostname === "www.litprofit.com" ||
      url.hostname === "localhost" || url.hostname === "127.0.0.1";
    return ok ? url.origin + url.pathname : undefined;
  } catch { return undefined; }
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  const auth = req.headers.get("Authorization") || "";
  const url = Deno.env.get("SUPABASE_URL")!;
  const admin = createClient(url, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  // Who is asking -- from the auth server, not from the request body.
  const token = auth.replace(/^Bearer\s+/i, "");
  const { data: who, error: whoErr } = await admin.auth.getUser(token);
  if (whoErr || !who?.user) return json({ error: "not signed in" }, 401);
  const me = who.user;
  const { data: myProfile } = await admin.from("profiles").select("role").eq("id", me.id).single();
  if (myProfile?.role !== "admin") return json({ error: "not allowed" }, 403);

  let body: Record<string, unknown> = {};
  try { body = await req.json(); } catch { /* empty is fine for list */ }
  const action = String(body.action || "list");
  const id = typeof body.id === "string" ? body.id : "";

  async function oneUser(uid: string) {
    const { data, error } = await admin.auth.admin.getUserById(uid);
    if (error || !data?.user) throw new Error("no such user");
    return data.user;
  }
  async function adminsLeft(except: string) {
    const { data } = await admin.from("profiles").select("id").eq("role", "admin").neq("id", except);
    const ids = (data || []).map((r: { id: string }) => r.id);
    let n = 0;
    for (const uid of ids) {
      const u = await oneUser(uid).catch(() => null);
      if (u && !isBlocked(u)) n++;
    }
    return n;
  }
  // banned_until is on the admin API's user object but not in the client's type
  const isBlocked = (u: unknown) => {
    const until = (u as { banned_until?: string | null }).banned_until;
    return !!until && new Date(until).getTime() > Date.now();
  };

  try {
    if (action === "list") {
      const users: Array<Record<string, unknown>> = [];
      for (let page = 1; page < 20; page++) {
        const { data, error } = await admin.auth.admin.listUsers({ page, perPage: 200 });
        if (error) throw error;
        users.push(...(data.users as unknown as Array<Record<string, unknown>>));
        if (data.users.length < 200) break;
      }
      const { data: profiles } = await admin.from("profiles").select("id,name,role");
      const byId = new Map((profiles || []).map((p: { id: string }) => [p.id, p]));
      return json({
        me: me.id,
        users: users.map((u) => {
          const p = byId.get(u.id as string) as { name?: string; role?: string } | undefined;
          return {
            id: u.id,
            email: u.email,
            name: p?.name || "",
            role: p?.role || "staff",
            created_at: u.created_at,
            last_sign_in_at: u.last_sign_in_at || null,
            blocked: isBlocked(u),
            // invited and has not yet chosen a password
            pending: !u.last_sign_in_at,
          };
        }),
      });
    }

    if (action === "create") {
      const email = String(body.email || "").trim().toLowerCase();
      const name = String(body.name || "").trim();
      const role = String(body.role || "staff");
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return json({ error: "bad email" }, 400);
      if (!ROLES.includes(role)) return json({ error: "bad role" }, 400);
      const { data, error } = await admin.auth.admin.generateLink({
        type: "invite",
        email,
        options: { data: { name }, redirectTo: safeRedirect(body.redirect) },
      });
      if (error) {
        const exists = /already|registered|exists/i.test(error.message);
        return json({ error: exists ? "exists" : error.message }, exists ? 409 : 400);
      }
      const uid = data.user!.id;
      // The trigger made the profile from the e-mail; give it the real name and role.
      await admin.from("profiles").update({ name: name || email.split("@")[0], role }).eq("id", uid);
      return json({ id: uid, link: data.properties?.action_link });
    }

    if (!id) return json({ error: "no user" }, 400);

    if (action === "link") {
      /* A fresh sign-in link for someone who never finished, or who forgot
         their password. An invited person who never opened theirs gets a new
         invite; anyone else a password-reset link. */
      const u = await oneUser(id);
      if (isBlocked(u)) return json({ error: "blocked" }, 409);
      const type = u.last_sign_in_at ? "recovery" : "invite";
      const { data, error } = await admin.auth.admin.generateLink({
        type, email: u.email!, options: { redirectTo: safeRedirect(body.redirect) },
      } as Parameters<typeof admin.auth.admin.generateLink>[0]);
      if (error) throw error;
      return json({ link: data.properties?.action_link, type });
    }

    if (action === "role") {
      const role = String(body.role || "");
      if (!ROLES.includes(role)) return json({ error: "bad role" }, 400);
      if (id === me.id && role !== "admin") return json({ error: "self" }, 409);
      if (role !== "admin") {
        const { data: p } = await admin.from("profiles").select("role").eq("id", id).single();
        if (p?.role === "admin" && (await adminsLeft(id)) < 1) return json({ error: "last admin" }, 409);
      }
      const { error } = await admin.from("profiles").update({ role }).eq("id", id);
      if (error) throw error;
      return json({ ok: true });
    }

    if (action === "name") {
      const name = String(body.name || "").trim().slice(0, 120);
      if (!name) return json({ error: "empty" }, 400);
      const { error } = await admin.from("profiles").update({ name }).eq("id", id);
      if (error) throw error;
      return json({ ok: true });
    }

    if (action === "block" || action === "unblock") {
      if (id === me.id) return json({ error: "self" }, 409);
      if (action === "block") {
        const { data: p } = await admin.from("profiles").select("role").eq("id", id).single();
        if (p?.role === "admin" && (await adminsLeft(id)) < 1) return json({ error: "last admin" }, 409);
      }
      const { error } = await admin.auth.admin.updateUserById(id, {
        ban_duration: action === "block" ? FOREVER : "none",
      });
      if (error) throw error;
      /* A block must take effect now, not when their token next expires:
         sign them out of every device. */
      if (action === "block") {
        await admin.rpc("users_end_sessions", { p_user: id }).then(() => {}, () => {});
      }
      return json({ ok: true });
    }

    return json({ error: "unknown action" }, 400);
  } catch (e) {
    return json({ error: (e as Error).message || "failed" }, 500);
  }
});

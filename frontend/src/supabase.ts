// Supabase client — real cloud persistence, wired but not faked.
// If VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY are not set at build time,
// this module exports null and the app keeps working on device storage.
// Nothing in the UI pretends cloud sync succeeded when it did not.
import { createClient, type SupabaseClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL as string | undefined
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined

export const supabaseConfigured = Boolean(url && anonKey)

export const supabase: SupabaseClient | null =
  supabaseConfigured && url && anonKey ? createClient(url, anonKey) : null

export async function signUp(email: string, password: string) {
  if (!supabase) throw new Error('Supabase is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY, then rebuild.')
  return supabase.auth.signUp({ email, password })
}

export async function signIn(email: string, password: string) {
  if (!supabase) throw new Error('Supabase is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY, then rebuild.')
  return supabase.auth.signInWithPassword({ email, password })
}

export async function signOut() {
  if (!supabase) return
  await supabase.auth.signOut()
}

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'http://127.0.0.1:54321';
const supabaseKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || 'local-anon-key';

export const isSupabaseConfigured = Boolean(
  import.meta.env.VITE_SUPABASE_URL && 
  import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY &&
  !import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY.includes('replace-with')
);

// Single client initialized once
export const supabase = createClient(supabaseUrl, supabaseKey);

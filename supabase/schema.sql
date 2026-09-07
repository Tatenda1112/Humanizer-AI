-- ============================================================
-- HumanizeAI — Supabase Schema
-- Paste this entire file into the Supabase SQL editor and run
-- ============================================================

-- 1. PROFILES (extends auth.users) ----------------------------
CREATE TABLE IF NOT EXISTS profiles (
  id                 UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email              TEXT,
  plan               TEXT DEFAULT 'free'  CHECK (plan IN ('free', 'basic', 'premium')),
  preferred_provider TEXT DEFAULT 'claude' CHECK (preferred_provider IN ('claude', 'openai')),
  words_used_today   INTEGER DEFAULT 0,
  words_used_month   INTEGER DEFAULT 0,
  last_reset_date    DATE    DEFAULT CURRENT_DATE,
  created_at         TIMESTAMPTZ DEFAULT NOW()
);

-- 2. HUMANIZATIONS --------------------------------------------
CREATE TABLE IF NOT EXISTS humanizations (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  original_text   TEXT NOT NULL,
  humanized_text  TEXT,
  provider        TEXT,
  model_used      TEXT,
  word_count      INTEGER,
  level           TEXT CHECK (level IN ('light', 'medium', 'aggressive')),
  tone            TEXT CHECK (tone IN ('academic', 'casual', 'professional', 'friendly', 'creative')),
  ai_score_before FLOAT,
  ai_score_after  FLOAT,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 3. SUBSCRIPTIONS --------------------------------------------
CREATE TABLE IF NOT EXISTS subscriptions (
  id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  stripe_customer_id     TEXT,
  stripe_subscription_id TEXT UNIQUE,
  plan                   TEXT,
  status                 TEXT,
  current_period_end     TIMESTAMPTZ,
  created_at             TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_humanizations_user_id   ON humanizations(user_id);
CREATE INDEX IF NOT EXISTS idx_humanizations_created   ON humanizations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id   ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_customer  ON subscriptions(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_profiles_plan           ON profiles(plan);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================
ALTER TABLE profiles       ENABLE ROW LEVEL SECURITY;
ALTER TABLE humanizations  ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions  ENABLE ROW LEVEL SECURITY;

-- profiles
CREATE POLICY "profiles: users read own"
  ON profiles FOR SELECT USING (auth.uid() = id);

CREATE POLICY "profiles: users update own"
  ON profiles FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "profiles: service role all"
  ON profiles FOR ALL USING (auth.role() = 'service_role');

-- humanizations
CREATE POLICY "humanizations: users read own"
  ON humanizations FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "humanizations: users insert own"
  ON humanizations FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "humanizations: service role all"
  ON humanizations FOR ALL USING (auth.role() = 'service_role');

-- subscriptions
CREATE POLICY "subscriptions: users read own"
  ON subscriptions FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "subscriptions: service role all"
  ON subscriptions FOR ALL USING (auth.role() = 'service_role');

-- ============================================================
-- TRIGGER — auto-create profile on signup
-- ============================================================
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO profiles (id, email)
  VALUES (NEW.id, NEW.email)
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();
